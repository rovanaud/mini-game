from django.urls import path

from apps.chat import views

urlpatterns = [
    path("rooms/<str:room_code>/", views.room_chat, name="room-chat"),
]
