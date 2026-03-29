import secrets
import string
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

import apps.adminops.types as event_types
from apps.adminops.events import log_event
from apps.identities.models import UserIdentity
from apps.rooms.models import (
    ConnectionStatus,
    Participant,
    ParticipantRoleAssignment,
    ParticipantStatus,
    RoleScopeType,
    RoleType,
    Room,
    RoomStatus,
    RoomTable,
    RoomVisibility,
    TableStatus,
    TableType,
)
from apps.rooms.selectors import get_participant_room_id

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

    log_event(
        event_types.ROOM_CREATED,
        room_id=room.room_id,
        participant_id=participant.participant_id,
        actor_identity_id=identity.identity_id,
        payload={"public_code": room.public_code},
    )

    ParticipantRoleAssignment.objects.create(
        participant=participant,
        role_type=RoleType.HOST,
        scope_type=RoleScopeType.ROOM,
        scope_id=room.room_id,
        granted_by_participant=None,  # self-granted at creation
    )

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
        log_event(
            event_types.ROOM_JOINED,
            room_id=room.room_id,
            participant_id=existing.participant_id,
            actor_identity_id=identity.identity_id,
            payload={"reconnect": True},
        )
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

    ParticipantRoleAssignment.objects.create(
        participant=participant,
        role_type=RoleType.SPECTATOR,
        scope_type=RoleScopeType.ROOM,
        scope_id=room.room_id,
        granted_by_participant=None,
    )

    log_event(
        event_types.ROOM_JOINED,
        room_id=room.room_id,
        participant_id=participant.participant_id,
        actor_identity_id=identity.identity_id,
        payload={"reconnect": False},
    )

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
    # TODO: We should also consider the case where the leaving participant is the host.
    # In that case, we might want to automatically assign a new host from the remaining
    # participants, or if there are no other participants, we could close the room. For
    # now, we'll just leave the host_participant field as is, but this is something we
    # should address in the future to ensure a good user experience.
    # TODO: Additionally, we might want to differentiate the circumstances of leaving,
    # such as voluntary leave vs. being kicked out vs. being disconnected due to
    # network issues. This could affect how we update the participant's status and how
    # we handle room state changes. For now, we'll just mark the participant as left
    # and disconnected expired, but in the future, we could have more nuanced handling
    # based on the reason for leaving.
    now = timezone.now()

    participant.status = ParticipantStatus.LEFT
    participant.connection_status = ConnectionStatus.DISCONNECTED_EXPIRED
    participant.left_at = now
    participant.save(update_fields=["status", "connection_status", "left_at"])

    room = participant.room
    room.last_activity_at = now
    room.save(update_fields=["last_activity_at", "updated_at"])

    log_event(
        event_types.ROOM_LEFT,
        room_id=get_participant_room_id(participant),
        participant_id=participant.participant_id,
        actor_identity_id=participant.identity.identity_id,
    )

    return participant
