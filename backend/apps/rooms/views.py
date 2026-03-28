import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from apps.games.models import GameDefinition
from apps.identities.services import create_guest_identity_and_session
from apps.matches.models import GameMatch
from apps.matches.runtime import initialize_match
from apps.matches.services import create_game_match
from apps.rooms.models import Participant, Room
from apps.rooms.selectors import get_room_participants
from apps.rooms.services import create_room, join_room

logger = logging.getLogger(__name__)


def _require_identity(request):
    if getattr(request, "identity", None) is None:
        return False
    return True


@require_GET
def home(request):
    games = GameDefinition.objects.order_by("display_name")
    context = {
        "identity": getattr(request, "identity", None),
        "games": games,
    }
    return render(request, "rooms/home.html", context)


@require_POST
def create_room_view(request):
    if request.identity is None:
        display_name = (request.POST.get("display_name") or "").strip() or None
        identity, guest_session, raw_token = create_guest_identity_and_session(
            display_name=display_name
        )
        request.identity = identity
    else:
        raw_token = None

    # room_name = (request.POST.get("room_name") or "").strip() or None

    room, participant, room_table = create_room(
        identity=request.identity,
    )

    logger.info(
        "room_created_from_home -> "
        "event : room_created_from_home"
        f"room_code : {room.public_code} | "
        f"participant_id : {str(participant.participant_id)} | "
        f"identity_id : {str(request.identity.identity_id)} | "
    )

    response = redirect("rooms:detail", room_code=room.public_code)
    if raw_token:
        response.set_cookie(
            "guest_session_token",
            raw_token,
            httponly=True,
            samesite="Lax",
            secure=False,
        )
    return response


@require_POST
def join_room_view(request):
    if request.identity is None:
        display_name = (request.POST.get("display_name") or "").strip() or None
        identity, guest_session, raw_token = create_guest_identity_and_session(
            display_name=display_name
        )
        request.identity = identity
    else:
        raw_token = None

    room_code = (request.POST.get("room_code") or "").strip().upper()

    room = get_object_or_404(Room, public_code=room_code)
    participant = join_room(
        room=room,
        identity=request.identity,
    )

    logger.info(
        "room_joined_from_home -> "
        "event : room_joined_from_home"
        f"room_code : {room.public_code} | "
        f"participant_id : {str(participant.participant_id)} | "
        f"identity_id : {str(request.identity.identity_id)} | "
    )

    response = redirect("rooms:detail", room_code=room.public_code)
    if raw_token:
        response.set_cookie(
            "guest_session_token",
            raw_token,
            httponly=True,
            samesite="Lax",
            secure=False,
        )
    return response


@require_GET
def room_detail(request, room_code):
    room = get_object_or_404(Room, public_code=room_code)
    participant = None
    if request.identity is not None:
        participant = Participant.objects.filter(
            room=room, identity=request.identity
        ).first()

    participants = get_room_participants(room)
    games = GameDefinition.objects.order_by("display_name")
    # TODO: there can be multiple active matches, take that into account
    active_match = (
        GameMatch.objects.filter(room=room)
        .exclude(state__in=["completed", "cancelled"])
        .order_by("-started_at")
        .first()
    )

    context = {
        "room": room,
        "participant": participant,
        "participants": participants,
        "games": games,
        "active_match": active_match,
    }
    return render(request, "rooms/detail.html", context)


@require_POST
def start_game_view(request, room_code):
    room = get_object_or_404(Room, public_code=room_code)

    if request.identity is None:
        messages.error(request, "Vous devez avoir une identité.")
        return redirect("rooms:home")

    creator = get_object_or_404(Participant, room=room, identity=request.identity)

    if not creator.is_host:
        messages.error(request, "Seul l'hôte peut démarrer une partie.")
        return redirect("rooms:detail", room_code=room.public_code)

    game_id = (request.POST.get("game_id") or "").strip()
    players_ids = request.POST.getlist("players_ids")
    game_match, match_table = create_game_match(
        room=room,
        game_id=game_id,
        created_by_participant=creator,
        players_ids=players_ids,
    )

    logger.info(
        "match_created_from_room -> "
        "event : match_created_from_room"
        f"room_code : {room.public_code} | "
        f"match_id : {str(game_match.game_match_id)} | "
        f"game_id : {game_id} | "
        f"participant_id : {str(creator.participant_id)} | "
        f"players : {players_ids} | "
    )

    initialize_match(game_match)

    return redirect("matches:detail", match_id=game_match.game_match_id)
