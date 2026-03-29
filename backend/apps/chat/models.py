import uuid

from django.db import models
from django.utils import timezone


class ChannelScopeType(models.TextChoices):
    ROOM = "room", "Room"
    TABLE = "table", "Table"
    MATCH = "match", "Match"
    TOURNAMENT = "tournament", "Tournament"


class SenderType(models.TextChoices):
    PARTICIPANT = "participant", "Participant"
    SYSTEM = "system", "System"


class MessageType(models.TextChoices):
    TEXT = "text", "Text"
    EMOJI = "emoji", "Emoji"
    REACTION = "reaction", "Reaction"
    SYSTEM = "system", "System"


class MessageStatus(models.TextChoices):
    CREATED = "created", "Created"
    DELIVERED = "delivered", "Delivered"
    EDITED = "edited", "Edited"
    DELETED = "deleted", "Deleted"


class ChatChannel(models.Model):
    channel_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        "rooms.Room",
        on_delete=models.CASCADE,
        related_name="chat_channels",
    )
    scope_type = models.CharField(max_length=32, choices=ChannelScopeType.choices)
    scope_id = models.UUIDField()
    channel_policy_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "chat_channel"
        constraints = [
            models.UniqueConstraint(
                fields=["scope_type", "scope_id"],
                name="uq_chat_channel_scope",
            )
        ]

    def __str__(self) -> str:
        return f"ChatChannel({self.scope_type}:{self.scope_id})"


class ChatMessage(models.Model):
    message_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender_type = models.CharField(
        max_length=16, choices=SenderType.choices, default=SenderType.PARTICIPANT
    )
    sender_id = models.UUIDField(
        null=True, blank=True
    )  # participant_id or None for system
    message_type = models.CharField(
        max_length=16, choices=MessageType.choices, default=MessageType.TEXT
    )
    status = models.CharField(
        max_length=16, choices=MessageStatus.choices, default=MessageStatus.CREATED
    )
    visibility_policy_json = models.JSONField(default=dict)
    payload_json = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "chat_message"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return (
            f"ChatMessage({self.sender_type}:{self.sender_id} @"
            f"{self.channel_id})"  # type: ignore[attr-defined]
        )
