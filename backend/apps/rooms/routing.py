from django.urls import re_path

from apps.rooms.consumers import RoomConsumer, RoomsUpdatesConsumer

websocket_urlpatterns = [
    re_path(r"^ws/rooms/updates/$", RoomsUpdatesConsumer.as_asgi()),  # type: ignore
    re_path(r"^ws/rooms/(?P<room_code>[A-Za-z0-9]+)/$", RoomConsumer.as_asgi()),  # type: ignore
]
