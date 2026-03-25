import uuid

from django.db import models


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
    resumable = models.BooleanField(default=False)
    termination_reason = models.CharField(max_length=128, null=True, blank=True)
    winner_summary_json = models.JSONField(null=True, blank=True)
    config_json = models.JSONField(default=dict)
    snapshot_state_json = models.JSONField(null=True, blank=True)
    metadata_json = models.JSONField(default=dict)

    class Meta:
        db_table = "game_match"
