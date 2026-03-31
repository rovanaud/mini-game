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
from apps.matches.errors import InvalidMatchStateError
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
    get_match_seats_with_participant_identity,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def initialize_match(game_match: GameMatch) -> GameMatch:
    if game_match.state not in [GameMatchState.DRAFT, GameMatchState.READY]:
        raise InvalidMatchStateError(
            f"Cannot initialize match from state={game_match.state}"
        )

    module = get_game_module(get_game_match_game_id(game_match))
    module.validate_config(game_match.config_json or {})

    seat_participant_ids = get_match_seat_participant_ids(game_match)
    seat_identities = get_match_seats_with_participant_identity(game_match)
    seat_identity_ids = [
        str(s.participant.identity_id) if s.participant else None
        for s in seat_identities
    ]

    context = GameSetupContext(
        match_id=str(game_match.game_match_id),
        room_id=str(get_game_match_room_id(game_match)),
        seat_participant_ids=seat_participant_ids,
        seat_identity_ids=seat_identity_ids,
    )

    initial_state = module.build_initial_state(game_match.config_json or {}, context)

    now = timezone.now()
    game_match.state = GameMatchState.ACTIVE
    game_match.started_at = now
    game_match.snapshot_state_json = initial_state
    game_match.save(
        update_fields=["state", "started_at", "snapshot_state_json", "updated_at"]
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
    game_match: GameMatch,
    participant_id: str,
    action_type: str,
    action_payload: dict,
) -> GameMatch:
    if game_match.state != GameMatchState.ACTIVE:
        raise InvalidMatchStateError(
            f"Cannot submit action on match with state={game_match.state}"
        )

    module = get_game_module(get_game_match_game_id(game_match))
    actor = get_actor_context(game_match, participant_id)

    current_state = game_match.snapshot_state_json or {}

    context = GameExecutionContext(
        match_id=str(game_match.game_match_id),
        room_id=str(get_game_match_room_id(game_match)),
        sequence_number=0,  # updated below
    )

    # Validate first — raises on invalid
    module.validate_action(current_state, action_type, action_payload, actor, context)

    # Determine next sequence number
    last_sequence = (
        GameMatchAction.objects.filter(game_match=game_match)
        .order_by("-sequence_number")
        .values_list("sequence_number", flat=True)
        .first()
    ) or 0
    next_sequence = last_sequence + 1
    context.sequence_number = next_sequence

    # Apply pure state transition
    result = module.apply_action(
        current_state, action_type, action_payload, actor, context
    )

    # Resolve outcome separately
    outcome = module.resolve_outcome(result.new_state, action_type, actor)

    # Persist action
    GameMatchAction.objects.create(
        game_match=game_match,
        sequence_number=next_sequence,
        actor_type=actor.actor_type,
        participant_id=participant_id,
        action_type=action_type,
        action_payload_json=action_payload,
        applied_at=timezone.now(),
    )

    # Persist snapshot + update match state
    last_snapshot_version = (
        MatchSnapshot.objects.filter(game_match=game_match)
        .order_by("-snapshot_version")
        .values_list("snapshot_version", flat=True)
        .first()
    ) or 1
    MatchSnapshot.objects.create(
        game_match=game_match,
        snapshot_version=last_snapshot_version + 1,
        state_json=result.new_state,
    )

    game_match.snapshot_state_json = result.new_state

    if outcome is not None:
        now = timezone.now()
        game_match.state = GameMatchState.COMPLETED
        game_match.ended_at = now
        game_match.winner_summary_json = outcome.winner_summary
        game_match.termination_reason = outcome.outcome_type
        game_match.save(
            update_fields=[
                "snapshot_state_json",
                "state",
                "ended_at",
                "winner_summary_json",
                "termination_reason",
                "updated_at",
            ]
        )

        log_event(
            event_types.MATCH_COMPLETED,
            room_id=get_game_match_room_id(game_match),
            match_id=game_match.game_match_id,
            participant_id=participant_id,
            actor_identity_id=actor.identity_id,
            payload={
                "outcome_type": outcome.outcome_type,
                "winner_summary": outcome.winner_summary,
                "final_sequence": next_sequence,
            },
        )
    else:
        game_match.save(update_fields=["snapshot_state_json", "updated_at"])

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

    return game_match


@transaction.atomic
def pause_match(game_match: GameMatch, participant_id: str) -> GameMatch:
    if game_match.state != GameMatchState.ACTIVE:
        raise InvalidMatchStateError(
            f"Cannot pause match with state={game_match.state}"
        )

    module = get_game_module(get_game_match_game_id(game_match))
    actor = get_actor_context(game_match, participant_id)

    if not module.can_pause(game_match.snapshot_state_json or {}, actor):
        raise InvalidMatchStateError("This game does not allow pausing.")

    now = timezone.now()
    game_match.state = GameMatchState.PAUSED
    game_match.paused_at = now
    game_match.resumable = True
    game_match.save(update_fields=["state", "paused_at", "resumable", "updated_at"])

    log_event(
        event_types.MATCH_PAUSED,
        room_id=get_game_match_room_id(game_match),
        match_id=game_match.game_match_id,
        participant_id=participant_id,
    )

    return game_match


@transaction.atomic
def resume_match(game_match: GameMatch, participant_id: str) -> GameMatch:
    if game_match.state != GameMatchState.PAUSED:
        raise InvalidMatchStateError(
            f"Cannot resume match with state={game_match.state}"
        )

    module = get_game_module(get_game_match_game_id(game_match))
    actor = get_actor_context(game_match, participant_id)

    if not module.can_resume(game_match.snapshot_state_json or {}, actor):
        raise InvalidMatchStateError("This game does not allow resuming.")

    game_match.state = GameMatchState.ACTIVE
    game_match.paused_at = None
    game_match.resumable = False
    game_match.save(update_fields=["state", "paused_at", "resumable", "updated_at"])

    return game_match


@transaction.atomic
def abandon_match(game_match: GameMatch, participant_id: str) -> GameMatch:
    if game_match.state not in [GameMatchState.ACTIVE, GameMatchState.PAUSED]:
        raise InvalidMatchStateError(
            f"Cannot abandon match with state={game_match.state}"
        )

    module = get_game_module(get_game_match_game_id(game_match))
    actor = get_actor_context(game_match, participant_id)

    if not module.can_abandon(game_match.snapshot_state_json or {}, actor):
        raise InvalidMatchStateError(
            "This game does not allow abandoning at this point."
        )

    now = timezone.now()
    game_match.state = GameMatchState.ABANDONED
    game_match.ended_at = now
    game_match.termination_reason = "abandoned"
    game_match.save(
        update_fields=["state", "ended_at", "termination_reason", "updated_at"]
    )

    log_event(
        event_types.MATCH_ABANDONED,
        room_id=get_game_match_room_id(game_match),
        match_id=game_match.game_match_id,
        participant_id=participant_id,
    )

    return game_match
