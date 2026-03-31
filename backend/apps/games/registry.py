from apps.games.connect_four.module import ConnectFourModule
from apps.games.empty_game.module import EmptyGameModule
from apps.games.errors import UnsupportedGameError
from apps.games.spi import GameModule
from apps.games.vowel_game.module import VowelGameModule

_GAME_MODULES: dict[str, GameModule] = {
    "empty_game": EmptyGameModule(),
    "vowel_game": VowelGameModule(),
    "connect_four": ConnectFourModule(),
}


def get_game_module(game_id: str) -> GameModule:
    try:
        return _GAME_MODULES[game_id]
    except KeyError as exc:
        raise UnsupportedGameError(f"Unsupported game key: {game_id}") from exc
