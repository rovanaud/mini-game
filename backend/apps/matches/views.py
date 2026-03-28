import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import select_template
from django.views.decorators.http import require_GET, require_POST

from apps.matches.models import GameMatch
from apps.matches.runtime import submit_action
from apps.matches.selectors import get_game_match_game_id
from apps.rooms.models import Participant

logger = logging.getLogger(__name__)


@require_GET
def match_detail(request, match_id):
    match = get_object_or_404(
        GameMatch.objects.select_related("room", "game", "created_by_participant"),
        game_match_id=match_id,
    )

    participant = None
    if request.identity is not None:
        participant = Participant.objects.filter(
            room=match.room, identity=request.identity
        ).first()

    participants = match.room.participants.select_related("identity").order_by(
        "joined_at"
    )
    state = match.snapshot_state_json or {}

    game_template_candidates = [
        f"matches/games/{get_game_match_game_id(match)}.html",
        "matches/games/_default.html",
    ]
    game_template = select_template(game_template_candidates).template.name

    context = {
        "match": match,
        "room": match.room,
        "game": match.game,
        "participant": participant,
        "participants": participants,
        "state": state,
        "game_template": game_template,
    }
    return render(request, "matches/detail.html", context)


@require_POST
def submit_match_action_view(request, match_id):
    match = get_object_or_404(
        GameMatch.objects.select_related("room", "game"), game_match_id=match_id
    )

    if request.identity is None:
        messages.error(request, "Identité requise.")
        return redirect("rooms:home")

    participant = Participant.objects.filter(
        room=match.room, identity=request.identity
    ).first()
    if participant is None:
        messages.error(request, "Vous ne participez pas à cette room.")
        return redirect("matches:detail", match_id=match_id)

    action_type = (request.POST.get("action_type") or "").strip()

    action_payload = {}
    if action_type == "play_vowel":
        action_payload["vowel"] = (request.POST.get("vowel") or "").strip()

    logger.info(
        "match_action_submitted_from_view",
        "event : match_action_submitted_from_view | "
        f"match_id :  {str(match.game_match_id)} | "
        f"participant_id :  {str(participant.participant_id)} | "
        f"action_type :  {action_type} | "
        f"action_payload :  {action_payload} | ",
    )

    try:
        submit_action(
            game_match=match,
            participant_id=str(participant.participant_id),
            action_type=action_type,
            action_payload=action_payload,
        )
        messages.success(request, "Action envoyée.")
    except Exception as exc:
        logger.warning(
            "match_action_submission_failed",
            "event : match_action_submission_failed | "
            f"match_id :  {str(match.game_match_id)} | "
            f"participant_id :  {str(participant.participant_id)} | "
            f"action_type :  {action_type} | "
            f"error :  {str(exc)} | ",
        )
        messages.error(request, str(exc))

    return redirect("matches:detail", match_id=match.game_match_id)
