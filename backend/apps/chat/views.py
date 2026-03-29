from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.chat.models import MessageType
from apps.chat.selectors import can_read_channel, get_channel_messages, get_room_channel
from apps.chat.services import get_or_create_room_channel, post_message
from apps.identities.services import create_guest_identity_and_session
from apps.rooms.models import Participant, Room


@require_GET
def get_room_chat(request, room_code):
    room = get_object_or_404(Room, public_code=room_code)
    identity = request.identity  # from GuestIdentityMiddleware

    if not identity:
        # Auto-join as guest if no identity yet
        identity, session, token = create_guest_identity_and_session()
        request.identity = identity
        identity = identity

    channel = get_room_channel(room)
    if not channel:
        # Room has no chat channel yet
        return JsonResponse({"messages": [], "channel_id": None})

    participant = get_object_or_404(Participant, room=room, identity=identity)
    if not can_read_channel(participant, channel):
        return JsonResponse({"error": "No access to this channel"}, status=403)

    messages = get_channel_messages(channel)
    return JsonResponse(
        {
            "channel_id": str(channel.channel_id),
            "messages": [
                {
                    "id": str(m.message_id),
                    "sender_type": m.sender_type,
                    "sender_id": m.sender_id,
                    "type": m.message_type,
                    "status": m.status,
                    "payload": m.payload_json,
                    "created_at": m.created_at.isoformat(),
                    "edited_at": m.edited_at.isoformat() if m.edited_at else None,
                    "deleted_at": m.deleted_at.isoformat() if m.deleted_at else None,
                }
                for m in messages
            ],
        }
    )


@require_POST
@csrf_exempt
def post_room_chat(request, room_code):
    # TODO: auth middleware ensures request.identity
    room = get_object_or_404(Room, public_code=room_code)
    identity = request.identity

    if not identity:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    participant = get_object_or_404(Participant, room=room, identity=identity)

    channel = get_room_channel(room) or get_or_create_room_channel(room)

    # TODO: parse text from body (JSON)
    import json

    body = json.loads(request.body.decode("utf-8"))
    text = body.get("text")

    message = post_message(
        channel=channel,
        sender=participant,
        text=text,
        message_type=MessageType.TEXT,
    )

    return JsonResponse(
        {
            "message": {
                "id": str(message.message_id),
                "sender_type": message.sender_type,
                "sender_id": str(message.sender_id),
                "type": message.message_type,
                "status": message.status,
                "payload": message.payload_json,
                "created_at": message.created_at.isoformat(),
                "edited_at": None,
                "deleted_at": None,
            }
        }
    )
