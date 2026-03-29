from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

import apps.adminops.types as event_types
from apps.adminops.events import log_event
from apps.games.registry import get_game_module
from apps.games.types import (
    GameExecutionContext,
    GameSetupContext,
)
from apps.matches.errors import (
    InvalidMatchStateError,
)
from apps.matches.models import (
    GameMatch,
    GameMatchAction,
    GameMatchState,
    MatchSnapshot,
)
from apps.matches.selectors import (
    get_actor_context,
    get_game_match_game_id,
    get_game_match_room_id,
    get_match_seat_participant_ids,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def initialize_match(game_match: GameMatch) -> GameMatch:
    if game_match.state not in [GameMatchState.DRAFT, GameMatchState.READY]:
        raise InvalidMatchStateError(
            f"Cannot initialize match from state={game_match.state}"
        )
    # TODO: Set a selector for the game_id
    module = get_game_module(get_game_match_game_id(game_match))
    module.validate_config(game_match.config_json or {})

    seat_participant_ids = get_match_seat_participant_ids(game_match)

    setup_context = GameSetupContext(
        match_id=str(game_match.game_match_id),
        room_id=str(get_game_match_room_id(game_match)),
        seat_participant_ids=seat_participant_ids,
    )

    initial_state = module.build_initial_state(
        config=game_match.config_json or {},
        context=setup_context,
    )

    now = timezone.now()
    game_match.state = GameMatchState.ACTIVE
    game_match.started_at = now
    game_match.snapshot_state_json = initial_state
    game_match.resumable = True
    game_match.save(
        update_fields=["state", "started_at", "snapshot_state_json", "resumable"]
    )

    MatchSnapshot.objects.create(
        game_match=game_match,
        snapshot_version=1,
        state_json=initial_state,
    )

    log_event(
        event_types.MATCH_STARTED,
        room_id=get_game_match_room_id(game_match),
        match_id=game_match.game_match_id,
        payload={
            "game_key": get_game_match_game_id(game_match),
            "seat_participant_ids": seat_participant_ids,
        },
    )

    return game_match


@transaction.atomic
def submit_action(
    *,
    game_match: GameMatch,
    participant_id: str,
    action_type: str,
    action_payload: dict,
) -> GameMatch:
    if game_match.state != GameMatchState.ACTIVE:
        raise InvalidMatchStateError("Only active matches can receive actions.")

    if not game_match.snapshot_state_json:
        raise InvalidMatchStateError("Match has no active snapshot state.")

    module = get_game_module(get_game_match_game_id(game_match))

    last_sequence = (
        GameMatchAction.objects.filter(game_match=game_match)
        .order_by("-sequence_number")
        .values_list("sequence_number", flat=True)
        .first()
    ) or 0
    next_sequence = last_sequence + 1

    actor = get_actor_context(game_match, participant_id)
    execution_context = GameExecutionContext(
        match_id=str(game_match.game_match_id),
        room_id=str(get_game_match_room_id(game_match)),
        sequence_number=next_sequence,
    )

    current_state = game_match.snapshot_state_json

    log_event(
        event_types.MATCH_ACTION_SUBMITTED,
        room_id=get_game_match_room_id(game_match),
        match_id=game_match.game_match_id,
        participant_id=participant_id,
        actor_identity_id=actor.identity_id,
        payload={
            "action_type": action_type,
            "sequence_number": next_sequence,
            "action_payload": action_payload,
        },
    )

    module.validate_action(
        state=current_state,
        action_type=action_type,
        action_payload=action_payload,
        actor=actor,
        context=execution_context,
    )
    result = module.apply_action(
        state=current_state,
        action_type=action_type,
        action_payload=action_payload,
        actor=actor,
        context=execution_context,
    )

    GameMatchAction.objects.create(
        game_match=game_match,
        sequence_number=next_sequence,
        actor_type="human",
        participant_id=participant_id,
        action_type=action_type,
        action_payload_json=action_payload,
        validated=True,
        applied_at=timezone.now(),
    )

    game_match.snapshot_state_json = result.new_state

    # Create a new snapshot
    # TODO: Optimize by setting a snapshotting frequency depending on the game
    last_snapshot_version = (
        MatchSnapshot.objects.filter(game_match=game_match)
        .order_by("-snapshot_version")
        .values_list("snapshot_version", flat=True)
        .first()
    ) or 0
    next_snapshot_version = last_snapshot_version + 1

    game_match.snapshot_state_json = result.new_state

    if result.is_terminal:
        game_match.state = GameMatchState.COMPLETED
        game_match.ended_at = timezone.now()
        game_match.winner_summary_json = result.winner_summary
        game_match.termination_reason = result.outcome_type or "completed"
        game_match.save(
            update_fields=[
                "snapshot_state_json",
                "state",
                "ended_at",
                "winner_summary_json",
                "termination_reason",
            ]
        )
        log_event(
            event_types.MATCH_COMPLETED,
            room_id=get_game_match_room_id(game_match),
            match_id=game_match.game_match_id,
            participant_id=participant_id,
            actor_identity_id=actor.identity_id,
            payload={
                "termination_reason": result.outcome_type or "completed",
                "winner_summary": result.winner_summary,
                "final_sequence": next_sequence,
            },
        )

    else:
        game_match.save(update_fields=["snapshot_state_json"])

    MatchSnapshot.objects.create(
        game_match=game_match,
        snapshot_version=next_snapshot_version,
        state_json=result.new_state,
    )

    return game_match
