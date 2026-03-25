import pytest
from apps.games.models import GameDefinition
from apps.identities.services import create_guest_identity_and_session
from apps.matches.services import (
    create_empty_game_match,
    move_participant_to_match_table,
    start_empty_game_match,
)
from apps.rooms.services import create_room, join_room

pytestmark = pytest.mark.django_db


def test_empty_game_vertical_slice_happy_path(empty_game_definition):
    assert GameDefinition.objects.filter(game_key="empty_game").exists(), (
        "empty_game must be seeded before running this test"
    )

    identity1, session1, token1 = create_guest_identity_and_session(
        display_name="Alice"
    )
    identity2, session2, token2 = create_guest_identity_and_session(display_name="Bob")

    room, host_participant, lobby = create_room(identity1)
    bob_participant = join_room(identity2, room)

    game_match, match_table = create_empty_game_match(
        room=room,
        created_by_participant=host_participant,
    )

    move_participant_to_match_table(host_participant, game_match)
    move_participant_to_match_table(bob_participant, game_match)

    start_empty_game_match(game_match)

    room.refresh_from_db()
    host_participant.refresh_from_db()
    bob_participant.refresh_from_db()
    game_match.refresh_from_db()
    match_table.refresh_from_db()

    assert room.participants.count() == 2
    assert room.game_matches.count() == 1
    assert game_match.state == "active"

    assert host_participant.current_game_match_id == game_match.pk
    assert bob_participant.current_game_match_id == game_match.pk
    assert host_participant.current_table_id == match_table.pk
    assert bob_participant.current_table_id == match_table.pk
