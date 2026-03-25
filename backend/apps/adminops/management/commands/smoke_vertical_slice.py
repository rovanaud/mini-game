from django.core.management.base import BaseCommand

from apps.identities.services import create_guest_identity_and_session
from apps.matches.services import (
    create_empty_game_match,
    move_participant_to_match_table,
    start_empty_game_match,
)
from apps.rooms.services import create_room, join_room


class Command(BaseCommand):
    help = "Run a minimal vertical slice smoke test"

    def handle(self, *args, **options):
        self.stdout.write("Starting smoke test...")

        identity1, session1, token1 = create_guest_identity_and_session(
            display_name="Alice"
        )
        identity2, session2, token2 = create_guest_identity_and_session(
            display_name="Bob"
        )

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
        game_match.refresh_from_db()

        self.stdout.write(self.style.SUCCESS("Smoke test completed."))
        self.stdout.write(f"Participants in room: {room.participants.count()}")
        self.stdout.write(f"Matches in room: {room.game_matches.count()}")
        self.stdout.write(f"Match state: {game_match.state}")
