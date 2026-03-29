from apps.chat.models import ChannelScopeType, ChatChannel, ChatMessage, MessageStatus
from apps.rooms.models import Participant
from apps.rooms.selectors import get_participant_room_id


def get_channel_room_id(channel: ChatChannel) -> str:
    return str(channel.room_id)  # type: ignore[attr-defined]


def get_channel_messages(
    channel: ChatChannel,
    *,
    exclude_deleted: bool = True,
    limit: int = 50,
) -> list[ChatMessage]:
    qs = ChatMessage.objects.filter(channel=channel)
    if exclude_deleted:
        qs = qs.exclude(status=MessageStatus.DELETED)
    return list(qs.order_by("created_at")[:limit])


def get_room_channel(room) -> ChatChannel | None:
    return ChatChannel.objects.filter(
        scope_type=ChannelScopeType.ROOM,
        scope_id=room.room_id,
    ).first()


def can_read_channel(participant: Participant, channel: ChatChannel) -> bool:
    """
    For now: any participant in the channel's room can read room-scoped channels.
    Match-scoped channels: only seated players.
    """
    if get_participant_room_id(participant) != get_channel_room_id(channel):
        return False
    if channel.scope_type == ChannelScopeType.MATCH:
        from apps.matches.models import GameMatchSeat

        return GameMatchSeat.objects.filter(
            game_match_id=channel.scope_id,
            participant=participant,
        ).exists()
    return True
