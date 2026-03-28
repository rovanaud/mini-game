import pytest
from apps.games.models import GameDefinition


@pytest.fixture
def empty_game_definition(db):
    game_definition, _ = GameDefinition.objects.get_or_create(
        game_id="empty_game",
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
    return game_definition
