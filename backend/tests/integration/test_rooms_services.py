import pytest
from apps.identities.services import create_guest_identity
from apps.matches.services import (
    create_empty_game_match,
)
from apps.rooms.models import ParticipantStatus
from apps.rooms.services import create_room, join_room, leave_room

pytestmark = pytest.mark.django_db


def test_join_room_returns_existing_participant_for_same_identity():
    host = create_guest_identity(display_name="Host")
    guest = create_guest_identity(display_name="Guest")

    room, host_participant, lobby = create_room(host)

    first_join = join_room(guest, room)
    second_join = join_room(guest, room)

    assert first_join.pk == second_join.pk
    assert room.participants.count() == 2


def test_leave_room_marks_participant_as_left():
    host = create_guest_identity(display_name="Host")
    guest = create_guest_identity(display_name="Guest")

    room, host_participant, lobby = create_room(host)
    participant = join_room(guest, room)

    leave_room(participant)
    participant.refresh_from_db()

    assert participant.status == ParticipantStatus.LEFT
    assert participant.left_at is not None


def test_create_empty_game_match_rejects_participant_from_other_room(
    empty_game_definition,
):
    host1 = create_guest_identity(display_name="Host1")
    host2 = create_guest_identity(display_name="Host2")

    room1, host_participant1, lobby1 = create_room(host1)
    room2, host_participant2, lobby2 = create_room(host2)

    with pytest.raises(
        ValueError, match="Participant does not belong to the given room"
    ):
        create_empty_game_match(
            room=room1,
            created_by_participant=host_participant2,
        )
