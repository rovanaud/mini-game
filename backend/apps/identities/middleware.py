from apps.identities.services import restore_guest_session

GUEST_SESSION_COOKIE_NAME = "guest_session_token"


class GuestIdentityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.identity = None

        raw_token = request.COOKIES.get(GUEST_SESSION_COOKIE_NAME)
        if raw_token:
            identity = restore_guest_session(raw_token)
            if identity is not None:
                request.identity = identity

        response = self.get_response(request)
        return response
