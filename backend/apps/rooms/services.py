import secrets
import string
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.identities.models import UserIdentity
from apps.rooms.models import (
    ConnectionStatus,
    Participant,
    ParticipantStatus,
    Room,
    RoomStatus,
    RoomTable,
    RoomVisibility,
    TableStatus,
    TableType,
)

DEFAULT_ROOM_INACTIVITY_MINUTES = 15


def _generate_room_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _generate_invite_token() -> str:
    return secrets.token_urlsafe(24)


def _generate_unique_room_code() -> str:
    while True:
        code = _generate_room_code()
        if not Room.objects.filter(public_code=code).exists():
            return code


def _generate_unique_invite_token() -> str:
    while True:
        token = _generate_invite_token()
        if not Room.objects.filter(invite_token=token).exists():
            return token


@transaction.atomic
def create_room(
    identity: UserIdentity,
    *,
    settings: dict | None = None,
    visibility: str = RoomVisibility.PRIVATE,
) -> tuple[Room, Participant, RoomTable]:
    now = timezone.now()
    room_settings = settings or {}

    room = Room.objects.create(
        public_code=_generate_unique_room_code(),
        invite_token=_generate_unique_invite_token(),
        status=RoomStatus.OPEN,
        visibility=visibility,
        created_by_identity=identity,
        last_activity_at=now,
        expires_at=now + timedelta(minutes=DEFAULT_ROOM_INACTIVITY_MINUTES),
        settings_json=room_settings,
    )

    lobby_table = RoomTable.objects.create(
        room=room,
        table_type=TableType.LOBBY,
        name="Lobby",
        status=TableStatus.OPEN,
    )

    participant = Participant.objects.create(
        room=room,
        identity=identity,
        status=ParticipantStatus.IDLE,
        connection_status=ConnectionStatus.CONNECTED,
        current_table=lobby_table,
        is_host=True,
        last_active_at=now,
    )

    room.host_participant = participant
    room.save(update_fields=["host_participant", "updated_at"])

    return room, participant, lobby_table


@transaction.atomic
def join_room(
    identity: UserIdentity,
    room: Room,
) -> Participant:
    now = timezone.now()

    existing = (
        Participant.objects.select_for_update()
        .filter(
            room=room,
            identity=identity,
            status__in=[
                ParticipantStatus.JOINING,
                ParticipantStatus.IDLE,
                ParticipantStatus.SPECTATING,
                ParticipantStatus.WAITING,
                ParticipantStatus.PLAYING,
            ],
        )
        .first()
    )
    if existing:
        existing.connection_status = ConnectionStatus.CONNECTED
        existing.last_active_at = now
        if existing.status == ParticipantStatus.JOINING:
            existing.status = ParticipantStatus.IDLE
        existing.save(update_fields=["connection_status", "last_active_at", "status"])
        return existing

    lobby_table = (
        RoomTable.objects.select_for_update()
        .filter(
            room=room,
            table_type=TableType.LOBBY,
            status__in=[TableStatus.OPEN, TableStatus.ACTIVE],
        )
        .first()
    )
    if lobby_table is None:
        lobby_table = RoomTable.objects.create(
            room=room,
            table_type=TableType.LOBBY,
            name="Lobby",
            status=TableStatus.OPEN,
        )

    participant = Participant.objects.create(
        room=room,
        identity=identity,
        status=ParticipantStatus.IDLE,
        connection_status=ConnectionStatus.CONNECTED,
        current_table=lobby_table,
        is_host=False,
        last_active_at=now,
    )

    room.last_activity_at = now
    room.status = (
        RoomStatus.ACTIVE
        if room.status in [RoomStatus.OPEN, RoomStatus.IDLE]
        else room.status
    )
    room.expires_at = now + timedelta(minutes=DEFAULT_ROOM_INACTIVITY_MINUTES)
    room.save(update_fields=["last_activity_at", "status", "expires_at", "updated_at"])

    return participant


def get_room_for_join(
    *, public_code: str | None = None, invite_token: str | None = None
) -> Room | None:
    if invite_token:
        return Room.objects.filter(invite_token=invite_token).first()
    if public_code:
        return Room.objects.filter(public_code=public_code).first()
    return None


@transaction.atomic
def leave_room(participant: Participant) -> Participant:
    now = timezone.now()

    participant.status = ParticipantStatus.LEFT
    participant.connection_status = ConnectionStatus.DISCONNECTED_EXPIRED
    participant.left_at = now
    participant.save(update_fields=["status", "connection_status", "left_at"])

    room = participant.room
    room.last_activity_at = now
    room.save(update_fields=["last_activity_at", "updated_at"])

    return participant
