from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.identities.middleware import GUEST_SESSION_COOKIE_NAME
from apps.identities.services import create_guest_identity_and_session


@require_http_methods(["GET", "POST"])
def guest_start(request):
    if request.method == "GET":
        if request.identity is not None:
            return redirect("rooms:home")
        return render(request, "identities/guest_start.html")

    display_name = request.POST.get("display_name", "").strip() or None

    identity, guest_session, raw_token = create_guest_identity_and_session(
        display_name=display_name,
        client_fingerprint=None,
    )

    response = redirect("rooms:home")
    response.set_cookie(
        GUEST_SESSION_COOKIE_NAME,
        raw_token,
        httponly=True,
        samesite="Lax",
        secure=False,  # passe à True en prod HTTPS
    )
    return response
