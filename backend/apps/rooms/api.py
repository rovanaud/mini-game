from __future__ import annotations

import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.chat.models import MessageType
from apps.chat.services import get_or_create_room_channel, post_message
from apps.games.models import GameDefinition
from apps.identities.services import create_guest_identity_and_session
from apps.matches.models import GameMatch
from apps.rooms.models import (
    Participant,
    ParticipantStatus,
    Proposal,
    ProposalResponse,
    ProposalResponseChoice,
    ProposalState,
    Room,
)
from apps.rooms.realtime import broadcast_room_event, room_group_name
from apps.rooms.selectors import get_room_participants, is_room_host
from apps.rooms.services import (
    create_proposal,
    create_room,
    join_room,
    leave_room,
    respond_to_proposal,
    serialize_proposal,
)

# logger = logging.getLogger(__name__)


def _post_room_system_message(room: Room, text: str):
    channel = get_or_create_room_channel(room)
    message = post_message(
        channel=channel,
        sender=None,
        text=text,
        message_type=MessageType.SYSTEM,
    )
    channel_layer = get_channel_layer()
    if channel_layer is not None:
        async_to_sync(channel_layer.group_send)(
            room_group_name(room.public_code),
            {
                "type": "room_chat_message",
                "message": {
                    "id": str(message.message_id),
                    "sender_id": None,
                    "display_name": "System",
                    "text": message.payload_json.get("text", ""),
                    "created_at": message.created_at.isoformat(),
                },
            },
        )
    return message


def _display_name(participant: Participant) -> str:
    if participant.identity and participant.identity.display_name:
        return participant.identity.display_name
    return f"Player {participant.participant_id}"


def _game_display_name(game_id: str) -> str:
    game = GameDefinition.objects.filter(game_id=game_id).first()
    return game.display_name if game else game_id


@csrf_exempt
@require_POST
def api_rename_room(request, room_code):
    """POST /api/rooms/<room_code>/rename/ — body: { name: str }. Host only."""
    room = get_object_or_404(Room, public_code=room_code)

    if request.identity is None:
        return JsonResponse({"error": "Identity required."}, status=401)

    participant = Participant.objects.filter(
        room=room, identity=request.identity
    ).first()
    if not participant or not participant.is_host:
        return JsonResponse({"error": "Only the host can rename the room."}, status=403)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    name = (body.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "name is required."}, status=400)

    room.name = name
    room.save(update_fields=["name", "updated_at"])
    broadcast_room_event(room, event="room_renamed", payload={"name": room.name})

    return JsonResponse({"name": room.name})


@require_GET
def api_room_list(request):
    """GET /rooms/api/ — rooms the current identity has joined."""
    if request.identity is None:
        return JsonResponse({"rooms": []})

    active_statuses = [
        ParticipantStatus.JOINING,
        ParticipantStatus.IDLE,
        ParticipantStatus.SPECTATING,
        ParticipantStatus.WAITING,
        ParticipantStatus.PLAYING,
    ]
    participants = (
        Participant.objects.filter(identity=request.identity)
        .select_related("room")
        .filter(status__in=active_statuses)
        .order_by("-room__created_at")
    )

    return JsonResponse(
        {
            "rooms": [
                {
                    "room_id": str(p.room.room_id),
                    "public_code": p.room.public_code,
                    "name": p.room.name,
                    "created_at": p.room.created_at.isoformat(),
                    "participant_count": Participant.objects.filter(
                        room=p.room, status__in=active_statuses
                    ).count(),
                }
                for p in participants
            ]
        }
    )


@require_GET
def api_room_detail(request, room_code):
    """GET /rooms/api/<room_code>/ — room info + participants + active match."""
    room = get_object_or_404(Room, public_code=room_code)
    participants = get_room_participants(room)

    my_participant = None
    if request.identity is not None:
        my_participant = Participant.objects.filter(
            room=room, identity=request.identity
        ).first()

    active_match = (
        GameMatch.objects.filter(room=room)
        .exclude(state__in=["completed", "cancelled", "abandoned"])
        .order_by("-started_at")
        .first()
    )

    games = list(
        GameDefinition.objects.order_by("display_name").values(
            "game_id", "display_name"
        )
    )
    open_proposals = list(
        Proposal.objects.filter(room=room, state=ProposalState.OPEN)
        .select_related("created_by_participant__identity")
        .order_by("-created_at")
    )
    pending_proposals = []
    for proposal in open_proposals:
        row = None
        if my_participant is not None:
            row = ProposalResponse.objects.filter(
                proposal=proposal, participant=my_participant
            ).first()
        data = serialize_proposal(proposal)
        data["my_response"] = row.response if row else None
        data["can_respond"] = (
            row is not None and row.response == ProposalResponseChoice.PENDING
        )
        pending_proposals.append(data)

    return JsonResponse(
        {
            "room_id": str(room.room_id),
            "public_code": room.public_code,
            "name": room.name,
            "is_host": my_participant.is_host if my_participant else False,
            "participants": [
                {
                    "participant_id": str(p.participant_id),
                    "display_name": p.identity.display_name if p.identity else None,
                    "is_me": (
                        my_participant is not None
                        and p.participant_id == my_participant.participant_id
                    ),
                    "is_host": p.is_host,
                }
                for p in participants
            ],
            # TODO: possibly many active matches in a room
            "active_match_id": str(active_match.game_match_id)
            if active_match
            else None,
            "my_participant_id": str(my_participant.participant_id)
            if my_participant
            else None,
            "available_games": games,
            "pending_proposals": pending_proposals,
        }
    )


@csrf_exempt
@require_POST
def api_create_room(request):
    """POST /rooms/api/create/ — body: { display_name?: str }"""
    try:
        body = json.loads(request.body) if request.body else {}
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    raw_token = None
    if request.identity is None:
        display_name = (body.get("display_name") or "").strip() or None
        identity, _, raw_token = create_guest_identity_and_session(
            display_name=display_name
        )
        request.identity = identity

    room, participant, _ = create_room(identity=request.identity)
    broadcast_room_event(room, event="room_created")

    response = JsonResponse(
        {
            "room_id": str(room.room_id),
            "public_code": room.public_code,
            "name": room.name,
            "participant_id": str(participant.participant_id),
        },
        status=201,
    )

    if raw_token:
        response.set_cookie(
            "guest_session_token",
            raw_token,
            httponly=True,
            samesite="Lax",
            secure=False,
        )
    return response


@csrf_exempt
@require_POST
def api_join_room(request):
    """POST /rooms/api/join/ — body: { room_code: str, display_name?: str }"""
    try:
        body = json.loads(request.body) if request.body else {}
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    raw_token = None
    if request.identity is None:
        display_name = (body.get("display_name") or "").strip() or None
        identity, _, raw_token = create_guest_identity_and_session(
            display_name=display_name
        )
        request.identity = identity

    room_code = (body.get("room_code") or "").strip().upper()
    if not room_code:
        return JsonResponse({"error": "room_code is required."}, status=400)

    room = get_object_or_404(Room, public_code=room_code)

    try:
        participant = join_room(room=room, identity=request.identity)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    broadcast_room_event(
        room,
        event="participant_joined",
        payload={"participant_id": str(participant.participant_id)},
    )

    response = JsonResponse(
        {
            "room_id": str(room.room_id),
            "public_code": room.public_code,
            "name": room.name,
            "participant_id": str(participant.participant_id),
        }
    )

    if raw_token:
        response.set_cookie(
            "guest_session_token",
            raw_token,
            httponly=True,
            samesite="Lax",
            secure=False,
        )
    return response


@csrf_exempt
@require_POST
def api_leave_room(request, room_code):
    """
    POST /api/rooms/<room_code>/leave/
    Marks current participant as left.
    Auto-deletes ephemeral rooms when no active participants remain.
    """
    room = get_object_or_404(Room, public_code=room_code)
    if request.identity is None:
        return JsonResponse({"error": "Identity required."}, status=401)

    participant = Participant.objects.filter(
        room=room, identity=request.identity
    ).first()
    if participant is None:
        return JsonResponse({"error": "Not a participant in this room."}, status=403)

    leave_room(participant)
    _post_room_system_message(room, f"{_display_name(participant)} left the room.")
    broadcast_room_event(
        room,
        event="participant_left",
        payload={"participant_id": str(participant.participant_id)},
    )

    active_count = Participant.objects.filter(
        room=room,
        status__in=[
            ParticipantStatus.JOINING,
            ParticipantStatus.IDLE,
            ParticipantStatus.SPECTATING,
            ParticipantStatus.WAITING,
            ParticipantStatus.PLAYING,
        ],
    ).count()

    deleted = False
    if active_count == 0 and not room.is_permanent:
        room.delete()
        deleted = True

    return JsonResponse({"ok": True, "deleted": deleted})


@csrf_exempt
@require_POST
def api_start_game(request, room_code):
    """
    POST /rooms/api/<room_code>/start/
    Body: { game_id: str, players_ids: str[] }
    Only the host can call this.
    """
    room = get_object_or_404(Room, public_code=room_code)

    if request.identity is None:
        return JsonResponse({"error": "Identity required."}, status=401)

    creator = Participant.objects.filter(room=room, identity=request.identity).first()
    if creator is None:
        return JsonResponse({"error": "Not a participant in this room."}, status=403)

    if not is_room_host(creator, room.room_id):
        return JsonResponse({"error": "Only the host can start a game."}, status=403)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    game_id = (body.get("game_id") or "").strip()
    players_ids = body.get("players_ids") or []

    if not game_id:
        return JsonResponse({"error": "game_id is required."}, status=400)

    try:
        proposal = create_proposal(
            room=room,
            created_by_participant=creator,
            proposal_type="match_start",
            payload={
                "game_id": game_id,
                "players_ids": players_ids,
                "voters_ids": players_ids,
            },
            rules={"mode": "all_or_nothing"},
        )
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    creator_name = _display_name(creator)
    targets = list(
        Participant.objects.filter(participant_id__in=players_ids).select_related(
            "identity"
        )
    )
    target_names = [
        name for name in [_display_name(p) for p in targets] if name != creator_name
    ]
    game_name = _game_display_name(game_id)
    if target_names:
        _post_room_system_message(
            room,
            f"{creator_name} proposed a {game_name} match"
            f" with {', '.join(target_names)}.",
        )
    else:
        _post_room_system_message(
            room,
            f"{creator_name} proposed a {game_name} match.",
        )

    broadcast_room_event(
        room,
        event="proposal_created",
        payload={"proposal": serialize_proposal(proposal)},
    )
    if proposal.state in {ProposalState.ACCEPTED, ProposalState.REJECTED}:
        broadcast_room_event(
            room,
            event="proposal_resolved",
            payload={"proposal": serialize_proposal(proposal)},
        )
    if proposal.state == ProposalState.ACCEPTED and proposal.result_json.get(
        "match_id"
    ):
        _post_room_system_message(room, f"{game_name} match started.")
        broadcast_room_event(
            room,
            event="match_started",
            payload={"match_id": proposal.result_json.get("match_id")},
        )

    return JsonResponse(
        {
            "proposal_id": str(proposal.proposal_id),
            "state": proposal.state,
            "match_id": proposal.result_json.get("match_id"),
        },
        status=201,
    )


@csrf_exempt
@require_POST
def api_respond_proposal(request, room_code, proposal_id):
    room = get_object_or_404(Room, public_code=room_code)
    proposal = get_object_or_404(Proposal, proposal_id=proposal_id, room=room)

    if request.identity is None:
        return JsonResponse({"error": "Identity required."}, status=401)

    participant = Participant.objects.filter(
        room=room, identity=request.identity
    ).first()
    if participant is None:
        return JsonResponse({"error": "Not a participant in this room."}, status=403)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    response_value = (body.get("response") or "").strip().lower()
    try:
        updated = respond_to_proposal(
            proposal=proposal,
            participant=participant,
            response=response_value,
        )
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    actor_name = _display_name(participant)
    if response_value == ProposalResponseChoice.YES:
        _post_room_system_message(room, f"{actor_name} accepted the proposal.")
    elif response_value == ProposalResponseChoice.NO:
        _post_room_system_message(room, f"{actor_name} declined the proposal.")
    elif response_value == ProposalResponseChoice.ABSTAIN:
        _post_room_system_message(room, f"{actor_name} abstained.")

    broadcast_room_event(
        room,
        event="proposal_updated",
        payload={"proposal": serialize_proposal(updated)},
    )

    if updated.state in {
        ProposalState.ACCEPTED,
        ProposalState.REJECTED,
        ProposalState.EXPIRED,
    }:
        broadcast_room_event(
            room,
            event="proposal_resolved",
            payload={"proposal": serialize_proposal(updated)},
        )

    if updated.state == ProposalState.ACCEPTED and updated.result_json.get("match_id"):
        game_id = str((updated.payload_json or {}).get("game_id", "Match"))
        _post_room_system_message(room, f"{_game_display_name(game_id)} match started.")
        broadcast_room_event(
            room,
            event="match_started",
            payload={"match_id": updated.result_json.get("match_id")},
        )

    return JsonResponse({"proposal": serialize_proposal(updated)})
