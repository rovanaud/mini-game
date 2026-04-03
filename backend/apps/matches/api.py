from __future__ import annotations

import json
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.matches.models import GameMatch
from apps.matches.runtime import submit_action
from apps.matches.selectors import (
    get_game_match_game_id,
    get_game_match_room_id,
    get_match_seats_with_participant_identity,
)
from apps.rooms.models import Participant

logger = logging.getLogger(__name__)


@require_GET
def api_match_detail(request, match_id):
    """
    GET /matches/api/<match_id>/
    Returns match state + seats + caller's seat index.
    """
    match = get_object_or_404(
        GameMatch.objects.select_related("room", "game"),
        game_match_id=match_id,
    )

    seats = get_match_seats_with_participant_identity(match)
    seats_data = [
        {
            "seat_index": s.seat_index,
            "participant_id": str(s.participant.participant_id),
            "display_name": (
                s.participant.identity.display_name
                if s.participant and s.participant.identity
                else None
            ),
            "actor_type": s.actor_type,
        }
        for s in seats
    ]

    my_seat_index = None
    if request.identity is not None:
        my_participant = Participant.objects.filter(
            room=match.room, identity=request.identity
        ).first()
        if my_participant:
            my_seat = seats.filter(participant=my_participant).first()
            if my_seat:
                my_seat_index = my_seat.seat_index

    return JsonResponse(
        {
            "match_id": str(match.game_match_id),
            "game_key": get_game_match_game_id(match),
            "room_id": get_game_match_room_id(match),
            "room_code": match.room.public_code,
            "game_config": match.config_json or {},
            "game_state": match.snapshot_state_json or {},
            "match_state": match.state,
            "seats": seats_data,
            "my_seat_index": my_seat_index,
        }
    )


@csrf_exempt
@require_POST
def api_submit_action(request, match_id):
    """
    POST /matches/api/<match_id>/actions/
    Body: { "action_type": str, "action_payload": dict }
    Returns updated game_state + match_state.
    """
    match = get_object_or_404(
        GameMatch.objects.select_related("room", "game"),
        game_match_id=match_id,
    )

    if request.identity is None:
        return JsonResponse({"error": "Identity required."}, status=401)

    participant = Participant.objects.filter(
        room=match.room, identity=request.identity
    ).first()
    if participant is None:
        return JsonResponse({"error": "Not a participant in this room."}, status=403)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    action_type = (body.get("action_type") or "").strip()
    action_payload = body.get("action_payload") or {}

    if not isinstance(action_payload, dict):
        return JsonResponse({"error": "action_payload must be an object."}, status=400)

    try:
        updated_match = submit_action(
            game_match=match,
            participant_id=str(participant.participant_id),
            action_type=action_type,
            action_payload=action_payload,
        )
    except Exception as exc:
        logger.warning(
            "api_action_failed | match=%s participant=%s action=%s error=%s",
            match_id,
            participant.participant_id,
            action_type,
            exc,
        )
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(
        {
            "match_state": updated_match.state,
            "game_state": updated_match.snapshot_state_json or {},
        }
    )
