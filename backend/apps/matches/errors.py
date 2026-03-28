class MatchError(Exception):
    """Base class for match-related errors."""


class MatchConfigurationError(MatchError):
    """The match is misconfigured or internally inconsistent."""


class InvalidMatchStateError(MatchError):
    """The match is not in a state compatible with the requested operation."""


class ActorNotInMatchError(MatchError):
    """The acting participant is not one of the match players."""
