from __future__ import annotations

import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.games.models import GameDefinition
from apps.identities.services import create_guest_identity_and_session
from apps.matches.models import GameMatch
from apps.matches.runtime import initialize_match
from apps.matches.selectors import get_game_match_game_id
from apps.matches.services import create_game_match
from apps.rooms.models import Participant, Room
from apps.rooms.selectors import get_room_participants, is_room_host
from apps.rooms.services import create_room, join_room

# logger = logging.getLogger(__name__)


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

    return JsonResponse({"name": room.name})


@require_GET
def api_room_list(request):
    """GET /rooms/api/ — rooms the current identity has joined."""
    if request.identity is None:
        return JsonResponse({"rooms": []})

    participants = (
        Participant.objects.filter(identity=request.identity)
        .select_related("room")
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
        game_match, _ = create_game_match(
            room=room,
            game_id=game_id,
            created_by_participant=creator,
            players_ids=players_ids,
        )
        initialize_match(game_match)
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(
        {
            "match_id": str(game_match.game_match_id),
            "game_key": get_game_match_game_id(game_match),
        },
        status=201,
    )
