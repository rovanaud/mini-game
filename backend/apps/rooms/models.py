import uuid

from django.db import models
from django.utils import timezone


class RoomStatus(models.TextChoices):
    CREATED = "created", "Created"
    OPEN = "open", "Open"
    ACTIVE = "active", "Active"
    IDLE = "idle", "Idle"
    CLOSING = "closing", "Closing"
    CLOSED = "closed", "Closed"
    EXPIRED = "expired", "Expired"
    ARCHIVED = "archived", "Archived"


class RoomVisibility(models.TextChoices):
    PRIVATE = "private", "Private"
    PUBLIC_FUTURE = "public_future", "Public (Future)"


class TableType(models.TextChoices):
    LOBBY = "lobby", "Lobby"
    MATCH = "match", "Match"
    TOURNAMENT = "tournament", "Tournament"
    CUSTOM = "custom", "Custom"


class TableStatus(models.TextChoices):
    OPEN = "open", "Open"
    ACTIVE = "active", "Active"
    IDLE = "idle", "Idle"
    CLOSED = "closed", "Closed"


class ParticipantStatus(models.TextChoices):
    JOINING = "joining", "Joining"
    IDLE = "idle", "Idle"
    SPECTATING = "spectating", "Spectating"
    WAITING = "waiting", "Waiting"
    PLAYING = "playing", "Playing"
    LEFT = "left", "Left"
    KICKED = "kicked", "Kicked"


class ConnectionStatus(models.TextChoices):
    CONNECTED = "connected", "Connected"
    DISCONNECTED_RECOVERABLE = "disconnected_recoverable", "Disconnected Recoverable"
    DISCONNECTED_EXPIRED = "disconnected_expired", "Disconnected Expired"


class Room(models.Model):
    room_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_permanent = models.BooleanField(default=False)
    name = models.CharField(max_length=128, default="Room Name")
    public_code = models.CharField(max_length=32, unique=True)
    invite_token = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=32, choices=RoomStatus.choices, default=RoomStatus.CREATED
    )
    visibility = models.CharField(
        max_length=32, choices=RoomVisibility.choices, default=RoomVisibility.PRIVATE
    )
    host_participant = models.ForeignKey(
        "rooms.Participant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hosted_rooms",
    )
    created_by_identity = models.ForeignKey(
        "identities.UserIdentity",
        on_delete=models.RESTRICT,
        related_name="created_rooms",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    close_reason = models.CharField(max_length=64, null=True, blank=True)
    settings_json = models.JSONField(default=dict)

    class Meta:
        db_table = "room"


class RoomTable(models.Model):
    table_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="tables")
    table_type = models.CharField(max_length=32, choices=TableType.choices)
    name = models.CharField(max_length=100)
    status = models.CharField(
        max_length=32, choices=TableStatus.choices, default=TableStatus.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    settings_json = models.JSONField(default=dict)

    class Meta:
        db_table = "room_table"


class Participant(models.Model):
    participant_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="participants"
    )
    identity = models.ForeignKey(
        "identities.UserIdentity",
        on_delete=models.RESTRICT,
        related_name="participants",
    )
    status = models.CharField(
        max_length=32,
        choices=ParticipantStatus.choices,
        default=ParticipantStatus.JOINING,
    )
    connection_status = models.CharField(
        max_length=32,
        choices=ConnectionStatus.choices,
        default=ConnectionStatus.CONNECTED,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_active_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    current_table = models.ForeignKey(
        RoomTable,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_participants",
    )
    current_game_match = models.ForeignKey(
        "matches.GameMatch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_participants",
    )
    is_host = models.BooleanField(default=False)
    metadata_json = models.JSONField(default=dict)

    class Meta:
        db_table = "participant"


class RoleType(models.TextChoices):
    HOST = "host", "Host"
    MODERATOR = "moderator", "Moderator"
    PLAYER = "player", "Player"
    SPECTATOR = "spectator", "Spectator"
    NARRATOR = "narrator", "Narrator"
    REFEREE = "referee", "Referee"


class RoleScopeType(models.TextChoices):
    ROOM = "room", "Room"
    TABLE = "table", "Table"
    MATCH = "match", "Match"
    TOURNAMENT = "tournament", "Tournament"
    GAME = "game", "Game"


class ParticipantRoleAssignment(models.Model):
    participant_role_assignment_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role_type = models.CharField(max_length=32, choices=RoleType.choices)
    scope_type = models.CharField(max_length=32, choices=RoleScopeType.choices)
    scope_id = models.UUIDField()
    granted_by_participant = models.ForeignKey(
        Participant,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="granted_role_assignments",
    )
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict)

    class Meta:
        db_table = "participant_role_assignment"
        constraints = [
            models.UniqueConstraint(
                fields=["participant", "role_type", "scope_type", "scope_id"],
                name="uq_participant_role_scope",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.participant_id}"  # type: ignore[attr-defined]
            f" | {self.role_type} @ {self.scope_type}:{self.scope_id}"
        )


class ProposalState(models.TextChoices):
    OPEN = "open", "Open"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class VoteMode(models.TextChoices):
    ALL_OR_NOTHING = "all_or_nothing", "All Or Nothing"
    MAJORITY = "majority", "Majority"


class ProposalResponseChoice(models.TextChoices):
    PENDING = "pending", "Pending"
    YES = "yes", "Yes"
    NO = "no", "No"
    ABSTAIN = "abstain", "Abstain"


class Proposal(models.Model):
    proposal_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="proposals")
    created_by_participant = models.ForeignKey(
        Participant,
        on_delete=models.RESTRICT,
        related_name="created_proposals",
    )
    proposal_type = models.CharField(max_length=64)
    state = models.CharField(
        max_length=32,
        choices=ProposalState.choices,
        default=ProposalState.OPEN,
    )
    payload_json = models.JSONField(default=dict)
    rules_json = models.JSONField(default=dict)
    result_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "proposal"


class ProposalResponse(models.Model):
    proposal_response_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="proposal_responses",
    )
    response = models.CharField(
        max_length=16,
        choices=ProposalResponseChoice.choices,
        default=ProposalResponseChoice.PENDING,
    )
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "proposal_response"
        constraints = [
            models.UniqueConstraint(
                fields=["proposal", "participant"],
                name="uq_proposal_participant_response",
            ),
        ]
