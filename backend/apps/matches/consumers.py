from __future__ import annotations

import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.identities.services import restore_guest_session
from apps.matches.models import GameMatch
from apps.matches.runtime import submit_action
from apps.matches.selectors import get_match_seats_with_participant_identity
from apps.rooms.models import Participant
from apps.rooms.realtime import room_group_name

logger = logging.getLogger(__name__)

GUEST_SESSION_COOKIE_NAME = "guest_session_token"


def _parse_cookies(headers: list[tuple[bytes, bytes]]) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for name, value in headers:
        if name == b"cookie":
            for part in value.decode("latin-1").split(";"):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    cookies[k.strip()] = v.strip()
    return cookies


class MatchConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for a single match.

    URL: /ws/matches/<match_id>/
    Group: match_<match_id>

    Incoming (client → server):
      { "type": "action",   "action_type": str, "action_payload": dict }
      { "type": "chat",     "text": str }
      { "type": "reaction", "emoji": str }

    Outgoing (server → client):
      { "type": "state_update",  "game_state": dict, "match_state": str,
        "seats": list, "my_seat_index": int | null }
      {
        "type": "chat_message",
        "message": { id, sender_id, display_name, text, created_at }
      }
      { "type": "reaction",      "sender_id": str, "emoji": str }
      { "type": "error",         "message": str }
    """

    # ── Lifecycle ────────────────────────────────────────────────────────────

    async def connect(self):
        self.match_id: str = self.scope["url_route"]["kwargs"]["match_id"]  # type: ignore
        self.group_name: str = f"match_{self.match_id}"
        self.identity = None
        self.participant = None

        cookies = _parse_cookies(self.scope.get("headers", []))  # type: ignore
        raw_token = cookies.get(GUEST_SESSION_COOKIE_NAME)
        if raw_token:
            result = await sync_to_async(restore_guest_session)(raw_token)
            if result:
                self.identity, _ = result

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Push current state immediately so the client doesn't need an HTTP
        # round-trip after connecting.
        try:
            match = await self._get_match()
            self.participant = await self._get_participant(match)
            state_push: dict = {
                "type": "state_update",
                "game_state": match.snapshot_state_json or {},
                "match_state": match.state,
                "seats": await self._serialize_seats(match),
                "my_seat_index": await self._get_my_seat_index(match),
            }
            if match.state == "completed":
                state_push["outcome"] = {
                    "termination_reason": match.termination_reason,
                    "winner_summary": match.winner_summary_json or {},
                    # Actor is null on initial push since we don't know the
                    # participant's role until they take an action.
                    "actor_participant_id": None,
                }
            await self.send_json(state_push)
        except Exception as exc:
            logger.warning(
                "ws_connect_state_push_failed | match=%s error=%s",
                self.match_id,
                exc,
            )

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # ── Incoming messages ────────────────────────────────────────────────────

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type")

        if msg_type == "action":
            await self._handle_action(content)
        elif msg_type == "chat":
            await self._handle_chat(content)
        elif msg_type == "reaction":
            await self._handle_reaction(content)
        elif msg_type == "request_rematch":
            await self._handle_rematch(content)
        else:
            await self.send_json(
                {
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                }
            )

    # ── Handlers ─────────────────────────────────────────────────────────────

    async def _handle_action(self, content: dict):
        if self.identity is None or self.participant is None:
            await self.send_json({"type": "error", "message": "Not authenticated."})
            return

        action_type = (content.get("action_type") or "").strip()
        action_payload = content.get("action_payload") or {}

        if not isinstance(action_payload, dict):
            await self.send_json(
                {"type": "error", "message": "action_payload must be an object."}
            )
            return

        try:
            match = await self._get_match()

            updated = await sync_to_async(submit_action)(
                game_match=match,
                participant_id=str(self.participant.participant_id),
                action_type=action_type,
                action_payload=action_payload,
            )

            event: dict = {
                "type": "broadcast_state_update",
                "game_state": updated.snapshot_state_json or {},
                "match_state": updated.state,
            }

            # If the match just ended, include outcome so each client can personalise
            if updated.state == "completed":
                event["outcome"] = {
                    "termination_reason": updated.termination_reason,
                    "winner_summary": updated.winner_summary_json or {},
                    # The participant who triggered this action
                    "actor_participant_id": str(self.participant.participant_id),
                }

            await self.channel_layer.group_send(self.group_name, event)
            await self.channel_layer.group_send(
                room_group_name(match.room.public_code),
                {
                    "type": "room_event",
                    "event": "match_state_updated",
                    "room_code": match.room.public_code,
                    "payload": {
                        "match_id": str(match.game_match_id),
                        "match_state": updated.state,
                        "action_type": action_type,
                    },
                },
            )
            if updated.state == "completed":
                await self.channel_layer.group_send(
                    room_group_name(match.room.public_code),
                    {
                        "type": "room_event",
                        "event": "match_completed",
                        "room_code": match.room.public_code,
                        "payload": {
                            "match_id": str(match.game_match_id),
                            "termination_reason": updated.termination_reason,
                            "winner_summary": updated.winner_summary_json or {},
                        },
                    },
                )
        except Exception as exc:
            await self.send_json({"type": "error", "message": str(exc)})
            return

    async def _handle_chat(self, content: dict):
        if self.identity is None or self.participant is None:
            await self.send_json({"type": "error", "message": "Not authenticated."})
            return

        text = (content.get("text") or "").strip()
        if not text:
            return

        try:
            message = await self._persist_chat_message(text)
        except Exception as exc:
            await self.send_json({"type": "error", "message": str(exc)})
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast_chat_message",
                "message": {
                    "id": str(message.message_id),
                    "sender_id": str(message.sender_id),
                    "display_name": (
                        self.participant.identity.display_name
                        if self.participant.identity
                        else None
                    ),
                    "text": message.payload_json.get("text", ""),
                    "created_at": message.created_at.isoformat(),
                },
            },
        )

    async def _handle_reaction(self, content: dict):
        if self.identity is None or self.participant is None:
            await self.send_json({"type": "error", "message": "Not authenticated."})
            return

        emoji = (content.get("emoji") or "").strip()
        if not emoji:
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast_reaction",
                "sender_id": str(self.participant.participant_id),
                "emoji": emoji,
            },
        )

    async def _handle_rematch(self, content: dict):
        from apps.matches.services import request_rematch

        try:
            match = await self._get_match()
            participant = await self._get_participant(match)
            if participant is None:
                await self.send_json({"type": "error", "message": "Not authenticated."})
                return
            else:
                participant_id = str(participant.participant_id)
                new_match = await sync_to_async(request_rematch)(match, participant_id)

        except Exception as exc:
            await self.send_json({"type": "error", "message": str(exc)})
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast_rematch",
                "rematch_match_id": str(new_match.game_match_id),
            },
        )
        await self.channel_layer.group_send(
            room_group_name(match.room.public_code),
            {
                "type": "room_event",
                "event": "match_rematch_started",
                "room_code": match.room.public_code,
                "payload": {
                    "previous_match_id": str(match.game_match_id),
                    "match_id": str(new_match.game_match_id),
                },
            },
        )

    # ── Group event handlers (channel layer → this socket) ───────────────────

    async def broadcast_state_update(self, event: dict):
        payload: dict = {
            "type": "state_update",
            "game_state": event["game_state"],
            "match_state": event["match_state"],
        }
        if "outcome" in event:
            payload["outcome"] = event["outcome"]
        await self.send_json(payload)

    async def broadcast_chat_message(self, event: dict):
        await self.send_json(
            {
                "type": "chat_message",
                "message": event["message"],
            }
        )

    async def broadcast_reaction(self, event: dict):
        await self.send_json(
            {
                "type": "reaction",
                "sender_id": event["sender_id"],
                "emoji": event["emoji"],
            }
        )

    async def broadcast_rematch(self, event: dict):
        await self.send_json(
            {
                "type": "rematch_request",
                "rematch_match_id": event["rematch_match_id"],
            }
        )

    # ── DB helpers ────────────────────────────────────────────────────────────

    @sync_to_async
    def _get_match(self) -> GameMatch:
        return GameMatch.objects.select_related("room", "game").get(
            game_match_id=self.match_id
        )

    @sync_to_async
    def _get_participant(self, match: GameMatch) -> Participant | None:
        if self.identity is None:
            return None
        return (
            Participant.objects.filter(room=match.room, identity=self.identity)
            .select_related("identity")
            .first()
        )

    @sync_to_async
    def _get_my_seat_index(self, match: GameMatch) -> int | None:
        if self.participant is None:
            return None
        from apps.matches.models import GameMatchSeat

        seat = GameMatchSeat.objects.filter(
            game_match=match, participant=self.participant
        ).first()
        return seat.seat_index if seat else None

    @sync_to_async
    def _serialize_seats(self, match: GameMatch) -> list[dict]:
        seats = get_match_seats_with_participant_identity(match)
        return [
            {
                "seat_index": s.seat_index,
                "participant_id": str(s.participant.participant_id)
                if s.participant
                else None,
                "display_name": (
                    s.participant.identity.display_name
                    if s.participant and s.participant.identity
                    else None
                ),
                "actor_type": s.actor_type,
            }
            for s in seats
        ]

    @sync_to_async
    def _persist_chat_message(self, text: str):
        from apps.chat.models import MessageType
        from apps.chat.services import get_or_create_match_channel, post_message

        match = GameMatch.objects.select_related("room").get(
            game_match_id=self.match_id
        )
        channel = get_or_create_match_channel(match)
        return post_message(
            channel=channel,
            sender=self.participant,
            text=text,
            message_type=MessageType.TEXT,
        )
