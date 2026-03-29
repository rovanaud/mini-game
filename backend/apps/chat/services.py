from django.db import transaction
from django.utils import timezone

import apps.adminops.types as event_types
from apps.adminops.events import log_event
from apps.chat.models import (
    ChannelScopeType,
    ChatChannel,
    ChatMessage,
    MessageStatus,
    MessageType,
    SenderType,
)
from apps.chat.selectors import get_channel_room_id
from apps.rooms.models import Participant, RoleType
from apps.rooms.selectors import (
    get_participant_identity_id,
    get_participant_room_id,
    has_room_role,
)


def get_or_create_room_channel(room) -> ChatChannel:
    channel, _ = ChatChannel.objects.get_or_create(
        scope_type=ChannelScopeType.ROOM,
        scope_id=room.room_id,
        defaults={"room": room},
    )
    return channel


def get_or_create_match_channel(match) -> ChatChannel:
    channel, _ = ChatChannel.objects.get_or_create(
        scope_type=ChannelScopeType.MATCH,
        scope_id=match.game_match_id,
        defaults={"room": match.room},
    )
    return channel


def _resolve_visibility_policy(
    channel: ChatChannel,
    sender: Participant | None,
) -> dict:
    """
    For now: all messages in a room channel are visible to all room members.
    Match channel messages are visible to seated players only.
    This will be replaced by VisibilityPolicyResolver when realtime is built.
    """
    if channel.scope_type == ChannelScopeType.MATCH:
        return {"scope": "match", "match_id": str(channel.scope_id)}
    return {"scope": "room", "room_id": get_channel_room_id(channel)}


@transaction.atomic
def post_message(
    *,
    channel: ChatChannel,
    sender: Participant | None,
    text: str,
    message_type: str = MessageType.TEXT,
) -> ChatMessage:
    if sender is not None and get_participant_room_id(sender) != get_channel_room_id(
        channel
    ):
        raise ValueError("Sender does not belong to this channel's room.")

    visibility = _resolve_visibility_policy(channel, sender)

    message = ChatMessage.objects.create(
        channel=channel,
        sender_type=SenderType.PARTICIPANT if sender else SenderType.SYSTEM,
        sender_id=sender.participant_id if sender else None,
        message_type=message_type,
        status=MessageStatus.CREATED,
        visibility_policy_json=visibility,
        payload_json={"text": text},
    )

    log_event(
        event_types.CHAT_MESSAGE_POSTED,
        room_id=get_channel_room_id(channel),
        participant_id=sender.participant_id if sender else None,
        actor_identity_id=get_participant_identity_id(sender) if sender else None,
        payload={
            "channel_id": str(channel.channel_id),
            "message_id": str(message.message_id),
            "scope_type": channel.scope_type,
        },
    )

    return message


@transaction.atomic
def edit_message(
    *,
    message: ChatMessage,
    editor: Participant,
    new_text: str,
) -> ChatMessage:
    if message.status == MessageStatus.DELETED:
        raise ValueError("Cannot edit a deleted message.")
    if str(message.sender_id) != str(editor.participant_id):
        raise ValueError("Only the original sender can edit a message.")

    now = timezone.now()
    message.payload_json = {"text": new_text}
    message.status = MessageStatus.EDITED
    message.edited_at = now
    message.save(update_fields=["payload_json", "status", "edited_at"])

    return message


@transaction.atomic
def delete_message(
    *,
    message: ChatMessage,
    deleted_by: Participant,
) -> ChatMessage:
    if message.status == MessageStatus.DELETED:
        return message

    # Allow sender OR room host/moderator to delete

    is_sender = str(message.sender_id) == str(deleted_by.participant_id)
    is_moderator = has_room_role(
        deleted_by, RoleType.MODERATOR, get_participant_room_id(deleted_by)
    ) or has_room_role(deleted_by, RoleType.HOST, get_participant_room_id(deleted_by))

    if not is_sender and not is_moderator:
        raise ValueError("Not authorized to delete this message.")

    now = timezone.now()
    message.status = MessageStatus.DELETED
    message.deleted_at = now
    message.save(update_fields=["status", "deleted_at"])

    return message
