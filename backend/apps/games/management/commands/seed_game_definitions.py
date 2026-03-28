from django.core.management.base import BaseCommand

from apps.games.default_games import EMPTY_GAME, VOWEL_GAME
from apps.games.models import GameDefinition


class Command(BaseCommand):
    help = "Seed initial game definitions"

    def handle(self, *args, **options):
        definitions = [
            ("empty_game", EMPTY_GAME),
            ("vowel_game", VOWEL_GAME),
        ]

        for game_id, payload in definitions:
            _game_definition, created = GameDefinition.objects.get_or_create(
                game_id=game_id,
                defaults=payload,
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created seed game definition: {game_id}")
                )
            else:
                self.stdout.write(f"Seed game definition already exists: {game_id}")
