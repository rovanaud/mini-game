from django.urls import path

from apps.matches import api

urlpatterns = [
    path("<uuid:match_id>/", api.api_match_detail),
    path("<uuid:match_id>/actions/", api.api_submit_action),
]
