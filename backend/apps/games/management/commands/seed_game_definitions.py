from django.core.management.base import BaseCommand

# from apps.games.default_games import EMPTY_GAME, VOWEL_GAME
from apps.games.models import GameDefinition
from apps.games.registry import _GAME_MODULES


class Command(BaseCommand):
    help = "Seed initial game definitions"

    def handle(self, *args, **options):
        definitions = [
            (key, game_module.get_metadata())
            for key, game_module in _GAME_MODULES.items()
        ]

        for game_id, payload in definitions:
            _game_definition, created = GameDefinition.objects.get_or_create(
                game_id=game_id,
                defaults=payload.__dict__,
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created seed game definition: {game_id}")
                )
            else:
                self.stdout.write(f"Seed game definition already exists: {game_id}")
