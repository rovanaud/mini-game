from __future__ import annotations

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.rooms.models import Room
from apps.rooms.selectors import get_room_participants_identities


def room_group_name(room_code: str) -> str:
    return f"room_{room_code.upper()}"


def identity_group_name(identity_id: str) -> str:
    return f"identity_{identity_id}"


def broadcast_room_event(
    room: Room,
    *,
    event: str,
    payload: dict | None = None,
) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    room_payload = payload or {}

    async_to_sync(channel_layer.group_send)(
        room_group_name(room.public_code),
        {
            "type": "room_event",
            "event": event,
            "room_code": room.public_code,
            "payload": room_payload,
        },
    )

    _broadcast_rooms_updated_for_room_identities(
        room,
        source_event=event,
        payload=room_payload,
    )


def _broadcast_rooms_updated_for_room_identities(
    room: Room,
    *,
    source_event: str,
    payload: dict,
) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    identity_ids = set(
        str(identity_id) for identity_id in get_room_participants_identities(room)
    )

    for identity_id in identity_ids:
        async_to_sync(channel_layer.group_send)(
            identity_group_name(identity_id),
            {
                "type": "rooms_event",
                "event": "rooms_updated",
                "room_code": room.public_code,
                "payload": {"source_event": source_event, **payload},
            },
        )
