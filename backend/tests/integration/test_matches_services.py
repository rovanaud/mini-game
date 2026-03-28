import pytest
from apps.identities.services import create_guest_identity
from apps.matches.services import (
    create_empty_game_match,
    move_participant_to_match_table,
    start_empty_game_match,
)
from apps.rooms.models import ParticipantStatus
from apps.rooms.selectors import (
    get_participant_current_game_match_id,
    get_participant_current_table_id,
)
from apps.rooms.services import create_room, join_room


def test_start_empty_game_match_fails_if_already_active(empty_game_definition):
    host = create_guest_identity(display_name="Host")
    room, host_participant, lobby = create_room(host)

    game_match, match_table = create_empty_game_match(
        room=room,
        created_by_participant=host_participant,
    )

    start_empty_game_match(game_match)

    game_match.refresh_from_db()

    with pytest.raises(ValueError, match="Cannot start match from state"):
        start_empty_game_match(game_match)


def test_move_participant_to_match_table_updates_participant_state(
    empty_game_definition,
):
    host = create_guest_identity(display_name="Host")
    guest = create_guest_identity(display_name="Guest")

    room, host_participant, lobby = create_room(host)
    guest_participant = join_room(guest, room)

    game_match, match_table = create_empty_game_match(
        room=room,
        created_by_participant=host_participant,
    )

    move_participant_to_match_table(guest_participant, game_match)
    guest_participant.refresh_from_db()

    assert get_participant_current_table_id(guest_participant) == match_table.pk
    assert get_participant_current_game_match_id(guest_participant) == game_match.pk
    assert guest_participant.status == ParticipantStatus.PLAYING
