from django.urls import path

from apps.identities import api

urlpatterns = [
    path("guest/", api.api_create_guest_identity),
    path("me/", api.api_me),
]
