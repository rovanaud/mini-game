# middleware.py
from django.utils import timezone

from apps.identities.services import refresh_guest_session, restore_guest_session

GUEST_SESSION_COOKIE_NAME = "guest_session_token"
REFRESH_THRESHOLD_DAYS = 2


class GuestIdentityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.identity = None
        request._new_guest_token = None

        raw_token = request.COOKIES.get(GUEST_SESSION_COOKIE_NAME)
        if raw_token:
            restored_data = restore_guest_session(raw_token)

            if restored_data is not None:
                identity, session = restored_data
                request.identity = identity
                if (
                    session
                    and (session.expires_at - timezone.now()).days
                    < REFRESH_THRESHOLD_DAYS
                ):
                    result = refresh_guest_session(raw_token)
                    if result:
                        _, new_raw_token = result
                        request._new_guest_token = new_raw_token

        response = self.get_response(request)

        if request._new_guest_token:
            response.set_cookie(
                GUEST_SESSION_COOKIE_NAME,
                request._new_guest_token,
                httponly=True,
                samesite="Lax",
                secure=False,  # True in prod
            )

        return response
