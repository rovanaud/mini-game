from django.db import transaction
from django.utils import timezone

from apps.games.models import GameDefinition
from apps.matches.models import GameMatch, GameMatchState
from apps.rooms.models import (
    Participant,
    ParticipantStatus,
    Room,
    RoomStatus,
    RoomTable,
    TableStatus,
    TableType,
)

EMPTY_GAME_KEY = "empty_game"


@transaction.atomic
def create_empty_game_match(
    *,
    room: Room,
    created_by_participant: Participant,
    config: dict | None = None,
) -> tuple[GameMatch, RoomTable]:
    if created_by_participant.room_id != room.room_id:
        raise ValueError("Participant does not belong to the given room.")

    game = GameDefinition.objects.filter(game_key=EMPTY_GAME_KEY).first()
    if game is None:
        raise ValueError("Empty game definition is missing. Seed it first.")

    match_table = RoomTable.objects.create(
        room=room,
        table_type=TableType.MATCH,
        name=f"Match {room.game_matches.count() + 1}",
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
    if game_match.game_id != EMPTY_GAME_KEY:
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
    if participant.room_id != game_match.room_id:
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

    return participant
