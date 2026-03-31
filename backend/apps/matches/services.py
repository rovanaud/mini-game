from django.db import transaction
from django.utils import timezone

import apps.adminops.types as event_types
from apps.adminops.events import log_event
from apps.games.models import GameDefinition
from apps.matches.models import (
    ActionActorType,
    GameMatch,
    GameMatchSeat,
    GameMatchState,
    SeatStatus,
)
from apps.matches.runtime import initialize_match
from apps.matches.selectors import get_game_match_game_id, get_game_match_room_id
from apps.rooms.models import (
    Participant,
    ParticipantRoleAssignment,
    ParticipantStatus,
    RoleScopeType,
    RoleType,
    Room,
    RoomStatus,
    RoomTable,
    TableStatus,
    TableType,
)
from apps.rooms.selectors import (
    get_participant_identity_id,
    get_participant_room_id,
    get_room_matches_count,
)

EMPTY_GAME_KEY = "empty_game"


@transaction.atomic
def create_empty_game_match(
    *,
    room: Room,
    created_by_participant: Participant,
    config: dict | None = None,
) -> tuple[GameMatch, RoomTable]:
    if get_participant_room_id(created_by_participant) != room.room_id:
        raise ValueError("Participant does not belong to the given room.")

    game = GameDefinition.objects.filter(game_id=EMPTY_GAME_KEY).first()
    if game is None:
        raise ValueError("Empty game definition is missing. Seed it first.")

    match_table = RoomTable.objects.create(
        room=room,
        table_type=TableType.MATCH,
        name=f"Match {get_room_matches_count(room) + 1}",
        status=TableStatus.OPEN,
    )

    game_match = GameMatch.objects.create(
        room=room,
        table=match_table,
        game=game,
        state=GameMatchState.DRAFT,
        created_by_participant=created_by_participant,
        resumable=True,
        config_json=config or {},
        snapshot_state_json={
            "type": "empty_game",
            "status": "initialized",
        },
    )

    return game_match, match_table


@transaction.atomic
def start_empty_game_match(game_match: GameMatch) -> GameMatch:
    if get_game_match_game_id(game_match) != EMPTY_GAME_KEY:
        raise ValueError("This service only starts the empty game.")
    if game_match.state not in [GameMatchState.DRAFT, GameMatchState.READY]:
        raise ValueError(f"Cannot start match from state={game_match.state}")

    now = timezone.now()

    game_match.state = GameMatchState.ACTIVE
    game_match.started_at = now
    game_match.snapshot_state_json = {
        "type": "empty_game",
        "status": "active",
        "started_at": now.isoformat(),
    }
    game_match.save(update_fields=["state", "started_at", "snapshot_state_json"])

    table = game_match.table
    table.status = TableStatus.ACTIVE
    table.save(update_fields=["status"])

    room = game_match.room
    room.status = RoomStatus.ACTIVE
    room.last_activity_at = now
    room.save(update_fields=["status", "last_activity_at", "updated_at"])

    return game_match


@transaction.atomic
def move_participant_to_match_table(
    participant: Participant,
    game_match: GameMatch,
) -> Participant:
    if get_participant_room_id(participant) != get_game_match_room_id(game_match):
        raise ValueError("Participant and match do not belong to the same room.")

    participant.current_table = game_match.table
    participant.current_game_match = game_match
    participant.status = ParticipantStatus.PLAYING
    participant.last_active_at = timezone.now()
    participant.save(
        update_fields=[
            "current_table",
            "current_game_match",
            "status",
            "last_active_at",
        ]
    )

    log_event(
        event_types.MATCH_JOINED_MATCH,
        room_id=get_game_match_room_id(game_match),
        match_id=game_match.game_match_id,
        participant_id=participant.participant_id,
        actor_identity_id=get_participant_identity_id(participant),
        payload={},
    )

    return participant


@transaction.atomic
def create_game_match(
    *,
    room: Room,
    created_by_participant: Participant,
    game_id: str,
    players_ids: list[str],
    config: dict | None = None,
) -> tuple[GameMatch, RoomTable]:
    # TODO : Verify if all participants are not currently in another active match
    if get_participant_room_id(created_by_participant) != str(room.room_id):
        raise ValueError("Participant does not belong to the given room. ")

    game = GameDefinition.objects.filter(game_id=game_id).first()
    if game is None:
        raise ValueError(f"Game definition not found for game_id={game_id}")

    if len(players_ids) < game.min_players or len(players_ids) > game.max_players:
        raise ValueError("Invalid seat participant count for this game.")

    normalized_participant_ids = [str(pid) for pid in players_ids]
    if len(set(normalized_participant_ids)) != len(normalized_participant_ids):
        raise ValueError("Duplicate participant IDs are not allowed.")

    players = list(
        Participant.objects.filter(
            participant_id__in=normalized_participant_ids, room=room
        )
    )

    players_by_id = {str(p.participant_id): p for p in players}
    missing_ids = [
        pid for pid in normalized_participant_ids if pid not in players_by_id
    ]
    if missing_ids:
        raise ValueError(f"Players do not belong to the room: {missing_ids}")

    existing_count = GameMatch.objects.filter(room=room).count()
    match_table = RoomTable.objects.create(
        room=room,
        table_type=TableType.MATCH,
        name=f"Match {existing_count + 1}",
        status=TableStatus.OPEN,
    )

    game_match = GameMatch.objects.create(
        room=room,
        table=match_table,
        game=game,
        state=GameMatchState.DRAFT,
        created_by_participant=created_by_participant,
        resumable=True,
        config_json=config or {},
        metadata_json={},
    )

    now = timezone.now()
    GameMatchSeat.objects.bulk_create(
        [
            GameMatchSeat(
                game_match=game_match,
                participant=players_by_id[pid],
                seat_index=index,
                actor_type=ActionActorType.HUMAN,
                seat_status=SeatStatus.FILLED,
                joined_at=now,
            )
            for index, pid in enumerate(normalized_participant_ids)
        ]
    )

    log_event(
        event_types.MATCH_CREATED,
        room_id=room.room_id,
        match_id=game_match.game_match_id,
        participant_id=created_by_participant.participant_id,
        actor_identity_id=get_participant_identity_id(created_by_participant),
        payload={
            "game_id": game_id,
            "player_count": len(players_ids),
            "player_ids": normalized_participant_ids,
        },
    )

    ParticipantRoleAssignment.objects.bulk_create(
        [
            ParticipantRoleAssignment(
                participant=players_by_id[pid],
                role_type=RoleType.PLAYER,
                scope_type=RoleScopeType.MATCH,
                scope_id=game_match.game_match_id,
                granted_by_participant=created_by_participant,
            )
            for pid in normalized_participant_ids
        ]
    )

    # Move participants to the match table
    for participant in players:
        move_participant_to_match_table(participant, game_match)

    return game_match, match_table


@transaction.atomic
def start_game_match(game_match: GameMatch) -> GameMatch:
    initialized = initialize_match(game_match)

    table = initialized.table
    table.status = TableStatus.ACTIVE
    table.save(update_fields=["status"])

    room = initialized.room
    room.status = RoomStatus.ACTIVE
    room.last_activity_at = timezone.now()
    room.save(update_fields=["status", "last_activity_at", "updated_at"])

    return initialized
