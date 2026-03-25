from django.core.management.base import BaseCommand

from apps.games.models import GameDefinition


class Command(BaseCommand):
    help = "Seed initial game definitions"

    def handle(self, *args, **options):
        game_definition, created = GameDefinition.objects.get_or_create(
            game_key="empty_game",
            defaults={
                "display_name": "Empty Game",
                "version": "1.0",
                "category": "system",
                "min_players": 1,
                "max_players": 8,
                "supports_spectators": True,
                "supports_pause": True,
                "supports_resume": True,
                "supports_bots": False,
                "supports_tournament": False,
                "supports_save_resume": True,
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS("Created seed game definition: empty_game")
            )
        else:
            self.stdout.write("Seed game definition already exists: empty_game")
