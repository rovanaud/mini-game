from __future__ import annotations

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.chat.models import MessageType
from apps.chat.services import get_or_create_room_channel, post_message
from apps.identities.services import restore_guest_session
from apps.rooms.models import Participant, Room
from apps.rooms.realtime import identity_group_name, room_group_name

GUEST_SESSION_COOKIE_NAME = "guest_session_token"


def _parse_cookies(headers: list[tuple[bytes, bytes]]) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for name, value in headers:
        if name == b"cookie":
            for part in value.decode("latin-1").split(";"):
                part = part.strip()
                if "=" in part:
                    key, raw_value = part.split("=", 1)
                    cookies[key.strip()] = raw_value.strip()
    return cookies


class RoomConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for room-level events.

    URL: /ws/rooms/<room_code>/
    Group: room_<ROOM_CODE>
    """

    async def connect(self):
        self.room_code: str = self.scope["url_route"]["kwargs"]["room_code"].upper()  # type: ignore
        self.group_name = room_group_name(self.room_code)
        self.room = None
        self.participant = None

        identity = await self._get_identity_from_cookie()
        if identity is None:
            await self.close(code=4401)
            return

        participant = await self._get_participant(identity_id=identity.identity_id)
        if participant is None:
            await self.close(code=4403)
            return

        self.participant = participant
        self.room = participant.room

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "type": "room_event",
                "event": "subscribed",
                "room_code": self.room_code,
                "payload": {},
            }
        )
        await self._send_recent_chat_history()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def room_event(self, event: dict):
        await self.send_json(
            {
                "type": "room_event",
                "event": event["event"],
                "room_code": event["room_code"],
                "payload": event.get("payload", {}),
            }
        )

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type")
        if msg_type == "chat":
            await self._handle_chat(content)
            return
        await self.send_json(
            {"type": "error", "message": f"Unknown message type: {msg_type}"}
        )

    async def _handle_chat(self, content: dict):
        if self.participant is None or self.room is None:
            await self.send_json({"type": "error", "message": "Not authenticated."})
            return

        text = (content.get("text") or "").strip()
        if not text:
            return

        message = await self._persist_chat_message(text)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "room_chat_message",
                "message": message,
            },
        )

    async def room_chat_message(self, event: dict):
        await self.send_json(
            {
                "type": "room_chat_message",
                "message": event["message"],
            }
        )

    async def _send_recent_chat_history(self):
        if self.room is None:
            return
        messages = await self._serialize_recent_room_messages()
        await self.send_json(
            {
                "type": "room_chat_history",
                "messages": messages,
            }
        )

    async def _get_identity_from_cookie(self):
        cookies = _parse_cookies(self.scope.get("headers", []))  # type: ignore
        raw_token = cookies.get(GUEST_SESSION_COOKIE_NAME)
        if not raw_token:
            return None
        result = await sync_to_async(restore_guest_session)(raw_token)
        if not result:
            return None
        identity, _ = result
        return identity

    @sync_to_async
    def _get_participant(self, *, identity_id):
        room = Room.objects.filter(public_code=self.room_code).first()
        if room is None:
            return None
        return (
            Participant.objects.filter(room=room, identity_id=identity_id)
            .select_related("identity", "room")
            .first()
        )

    @sync_to_async
    def _persist_chat_message(self, text: str) -> dict:
        channel = get_or_create_room_channel(self.room)
        message = post_message(
            channel=channel,
            sender=self.participant,
            text=text,
            message_type=MessageType.TEXT,
        )
        return self._serialize_message(message)

    @sync_to_async
    def _serialize_recent_room_messages(self) -> list[dict]:
        from apps.chat.selectors import get_channel_messages

        channel = get_or_create_room_channel(self.room)
        messages = get_channel_messages(channel, limit=50)
        return [self._serialize_message(message) for message in messages]

    def _serialize_message(self, message) -> dict:
        display_name = None
        if self.participant and self.participant.identity:
            if str(message.sender_id) == str(self.participant.participant_id):
                display_name = self.participant.identity.display_name
            else:
                sender = (
                    Participant.objects.filter(participant_id=message.sender_id)
                    .select_related("identity")
                    .first()
                )
                display_name = (
                    sender.identity.display_name if sender and sender.identity else None
                )
        return {
            "id": str(message.message_id),
            "sender_id": str(message.sender_id) if message.sender_id else None,
            "display_name": display_name,
            "text": message.payload_json.get("text", ""),
            "created_at": message.created_at.isoformat(),
        }


class RoomsUpdatesConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for identity-level rooms list invalidation events.

    URL: /ws/rooms/updates/
    Group: identity_<identity_id>
    """

    async def connect(self):
        identity = await self._get_identity_from_cookie()
        if identity is None:
            await self.close(code=4401)
            return

        self.group_name = identity_group_name(str(identity.identity_id))

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(
            {
                "type": "rooms_event",
                "event": "subscribed",
                "payload": {},
            }
        )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def rooms_event(self, event: dict):
        await self.send_json(
            {
                "type": "rooms_event",
                "event": event["event"],
                "room_code": event.get("room_code"),
                "payload": event.get("payload", {}),
            }
        )

    async def _get_identity_from_cookie(self):
        cookies = _parse_cookies(self.scope.get("headers", []))  # type: ignore
        raw_token = cookies.get(GUEST_SESSION_COOKIE_NAME)
        if not raw_token:
            return None
        result = await sync_to_async(restore_guest_session)(raw_token)
        if not result:
            return None
        identity, _ = result
        return identity
