# apps/matches/urls.py
from django.urls import path

from apps.matches import views

app_name = "matches"

urlpatterns = [
    path("<uuid:match_id>/", views.match_detail, name="detail"),
    path(
        "<uuid:match_id>/action/", views.submit_match_action_view, name="submit_action"
    ),
]
