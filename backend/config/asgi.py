"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Django ASGI app must be obtained before importing anything that touches models
django_asgi_app = get_asgi_application()

from apps.matches.routing import (
    websocket_urlpatterns as match_ws_urlpatterns,  # noqa: E402
)
from apps.rooms.routing import (
    websocket_urlpatterns as room_ws_urlpatterns,  # noqa: E402
)

websocket_urlpatterns = [*match_ws_urlpatterns, *room_ws_urlpatterns]

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns)),
    }
)
