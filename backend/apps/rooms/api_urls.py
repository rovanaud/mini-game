from django.urls import path

from apps.rooms import api

urlpatterns = [
    path("", api.api_room_list),
    path("create/", api.api_create_room),
    path("join/", api.api_join_room),
    path("<str:room_code>/", api.api_room_detail),
    path("<str:room_code>/start/", api.api_start_game),
    path(
        "<str:room_code>/proposals/<uuid:proposal_id>/respond/",
        api.api_respond_proposal,
    ),
    path("<str:room_code>/rename/", api.api_rename_room),
]
