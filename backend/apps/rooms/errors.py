class GuestNotAllowedError(Exception):
    """Raised when a guest attempts an action restricted to registered users."""


class RoomJoinNotAllowedError(Exception):
    """Raised when join-by-code is attempted on a permanent room."""


class NotARoomMemberError(Exception):
    """Raised when an identity is not a member of a permanent room."""
