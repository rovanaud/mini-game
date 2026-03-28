from apps.games.empty_game.module import EmptyGameGameModule
from apps.games.errors import UnsupportedGameError
from apps.games.spi import GameModule
from apps.games.vowel_game.module import VowelGameModule

_GAME_MODULES = {
    "empty_game": EmptyGameGameModule(),
    "vowel_game": VowelGameModule(),
}


def get_game_module(game_id: str) -> GameModule:
    try:
        return _GAME_MODULES[game_id]
    except KeyError as exc:
        raise UnsupportedGameError(f"Unsupported game key: {game_id}") from exc
