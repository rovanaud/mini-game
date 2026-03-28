# apps/rooms/urls.py
from django.urls import path

from apps.rooms import views

app_name = "rooms"

urlpatterns = [
    path("", views.home, name="home"),
    path("create/", views.create_room_view, name="create"),
    path("join/", views.join_room_view, name="join"),
    path("<str:room_code>/", views.room_detail, name="detail"),
    path("<str:room_code>/start-game/", views.start_game_view, name="start_game"),
]
