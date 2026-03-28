class GameError(Exception):
    """Base class for game-related errors."""


class UnsupportedGameError(GameError):
    """No game module exists for the given game key."""


class InvalidGameConfigError(GameError):
    """The provided game config is invalid."""


class InvalidGameActionError(GameError):
    """The submitted game action is invalid according to the game rules."""
