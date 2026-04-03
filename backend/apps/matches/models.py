import uuid

from django.db import models
from django.utils import timezone


class GameMatchState(models.TextChoices):
    DRAFT = "draft", "Draft"
    WAITING_FOR_PLAYERS = "waiting_for_players", "Waiting for Players"
    READY = "ready", "Ready"
    STARTING = "starting", "Starting"
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    INTERRUPTED = "interrupted", "Interrupted"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    ABANDONED = "abandoned", "Abandoned"
    ARCHIVED = "archived", "Archived"
    PENDING_ACCEPTANCE = "pending_acceptance", "Pending Acceptance"


class ActionActorType(models.TextChoices):
    HUMAN = "human", "Human"
    BOT = "bot", "Bot"


class SeatStatus(models.TextChoices):
    RESERVED = "reserved", "Reserved"
    FILLED = "filled", "Filled"
    VACATED = "vacated", "Vacated"
    REPLACED = "replaced", "Replaced"


class GameMatch(models.Model):
    game_match_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    room = models.ForeignKey(
        "rooms.Room", on_delete=models.CASCADE, related_name="game_matches"
    )
    table = models.ForeignKey(
        "rooms.RoomTable", on_delete=models.RESTRICT, related_name="game_matches"
    )
    game = models.ForeignKey(
        "games.GameDefinition", on_delete=models.RESTRICT, related_name="game_matches"
    )
    state = models.CharField(
        max_length=32, choices=GameMatchState.choices, default=GameMatchState.DRAFT
    )
    created_by_participant = models.ForeignKey(
        "rooms.Participant",
        on_delete=models.RESTRICT,
        related_name="created_game_matches",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True, auto_now=True)
    resumable = models.BooleanField(default=False)
    termination_reason = models.CharField(max_length=128, null=True, blank=True)
    winner_summary_json = models.JSONField(null=True, blank=True)
    config_json = models.JSONField(default=dict)
    snapshot_state_json = models.JSONField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict)
    pending_acceptances = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "game_match"


class GameMatchAction(models.Model):
    game_match_action_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    game_match = models.ForeignKey(
        "matches.GameMatch", on_delete=models.CASCADE, related_name="actions"
    )
    sequence_number = models.PositiveBigIntegerField()
    actor_type = models.CharField(
        max_length=16, choices=ActionActorType.choices, default=ActionActorType.HUMAN
    )
    participant_id = models.UUIDField()
    action_type = models.CharField(max_length=64)
    action_payload_json = models.JSONField(default=dict)
    validated = models.BooleanField(default=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    resulting_state_hash = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "game_match_action"
        constraints = [
            models.UniqueConstraint(
                fields=["game_match", "sequence_number"],
                name="uq_game_match_action_sequence",
            ),
        ]


class GameMatchSeat(models.Model):
    game_match = models.ForeignKey(
        "GameMatch",
        on_delete=models.CASCADE,
        related_name="seats",
    )
    seat_index = models.PositiveIntegerField()
    actor_type = models.CharField(
        max_length=16,
        choices=ActionActorType.choices,
        default=ActionActorType.HUMAN,
    )
    participant = models.ForeignKey(
        "rooms.Participant",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="game_match_seats",
    )
    bot_id = models.UUIDField(null=True, blank=True)
    team_index = models.PositiveSmallIntegerField(null=True, blank=True)
    seat_status = models.CharField(
        max_length=16,
        choices=SeatStatus.choices,
        default=SeatStatus.FILLED,
    )
    joined_at = models.DateTimeField(default=timezone.now)
    left_at = models.DateTimeField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["game_match", "seat_index"],
                name="uniq_game_match_seat_index",
            ),
            models.UniqueConstraint(
                fields=["game_match", "participant"],
                name="uniq_game_match_participant",
            ),
        ]
        ordering = ["seat_index"]

    def __str__(self) -> str:
        return (
            f"{self.game_match} seat={self.seat_index} participant={self.participant}"
        )


class MatchSnapshot(models.Model):
    match_snapshot_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    game_match = models.ForeignKey(
        "GameMatch",
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    snapshot_version = models.PositiveBigIntegerField()
    state_json = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "game_match_snapshot"
        constraints = [
            models.UniqueConstraint(
                fields=["game_match", "snapshot_version"],
                name="uq_game_match_snapshot_version",
            ),
        ]
        ordering = ["snapshot_version"]

    def __str__(self) -> str:
        return f"Snapshot v{self.snapshot_version} for match {self.game_match_id}"  # type: ignore[attr-defined]
