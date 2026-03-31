from django.db import models
from django.utils import timezone

from apps.identities.models import UserIdentity
from apps.matches.models import GameMatch
from apps.rooms.models import (
    Participant,
    ParticipantRoleAssignment,
    ParticipantStatus,
    RoleScopeType,
    RoleType,
    Room,
    RoomTable,
)


def get_room_participants(room: Room):
    return Participant.objects.filter(room=room).order_by("joined_at")


def get_room_participants_count(room: Room):
    return get_room_participants(room).count()


def get_room_participants_ids(room: Room):
    return get_room_participants(room).values_list("participant_id", flat=True)


def get_room_participants_identities(room: Room):
    return (
        get_room_participants(room)
        .select_related("identity")
        .values_list("identity", flat=True)
    )


def get_participant_room_id(participant: Participant) -> str:
    return str(participant.room_id)  # type: ignore[attr-defined]


def get_participant_identity_id(participant: Participant) -> str:
    return str(participant.identity_id)  # type: ignore[attr-defined]


def get_room_table_room_id(room_table: RoomTable) -> str:
    return str(room_table.room_id)  # type: ignore[attr-defined]


def get_room_matches(room: Room):
    return GameMatch.objects.filter(room=room).order_by("-started_at")


def get_room_matches_count(room: Room) -> int:
    return get_room_matches(room).count()


def get_participant_current_game_match_id(participant: Participant) -> str:
    return str(participant.current_game_match_id)  # type: ignore[attr-defined]


def get_participant_current_table_id(participant: Participant) -> str:
    return str(participant.current_table_id)  # type: ignore[attr-defined]


def has_room_role(participant: Participant, role_type: str, room_id: str) -> bool:
    now = timezone.now()
    return (
        ParticipantRoleAssignment.objects.filter(
            participant=participant,
            role_type=role_type,
            scope_type=RoleScopeType.ROOM,
            scope_id=room_id,
        )
        .filter(models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now))
        .exists()
    )


def is_room_host(participant: Participant, room_id) -> bool:
    return has_room_role(participant, RoleType.HOST, room_id)


def get_participant_roles(participant: Participant) -> list[ParticipantRoleAssignment]:
    return list(
        ParticipantRoleAssignment.objects.filter(participant=participant).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        )
    )


def get_permanent_rooms_for_identity(identity: UserIdentity) -> models.query.QuerySet:
    """
    Returns all permanent rooms where this identity is an active participant.
    Used by RoomsSpace.vue via GET /api/players/me/rooms/?permanent=true
    """
    return Room.objects.filter(
        is_permanent=True,
        participants__identity=identity,
        participants__status__in=[
            ParticipantStatus.IDLE,
            ParticipantStatus.WAITING,
            ParticipantStatus.PLAYING,
        ],
    ).order_by("-last_activity_at")
