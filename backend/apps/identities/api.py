from __future__ import annotations

import json

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.identities.middleware import GUEST_SESSION_COOKIE_NAME
from apps.identities.models import GuestSession, IdentityStatus
from apps.identities.services import create_guest_identity_and_session


def _serialize_identity(identity) -> dict:
    return {
        "identity_id": str(identity.identity_id),
        "display_name": identity.display_name,
        "identity_type": identity.identity_type,
        "status": identity.status,
        "avatar_url": identity.avatar_url,
        "created_at": identity.created_at.isoformat(),
    }


@csrf_exempt
@require_http_methods(["POST"])
def api_create_guest_identity(request):
    """
    POST /api/identities/guest/
    Body: { display_name?: str }
    """
    if request.identity is not None:
        return JsonResponse({"identity": _serialize_identity(request.identity)})

    try:
        body = json.loads(request.body) if request.body else {}
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    display_name = (body.get("display_name") or "").strip() or None

    identity, _, raw_token = create_guest_identity_and_session(
        display_name=display_name
    )

    response = JsonResponse({"identity": _serialize_identity(identity)}, status=201)
    response.set_cookie(
        GUEST_SESSION_COOKIE_NAME,
        raw_token,
        httponly=True,
        samesite="Lax",
        secure=False,
    )
    return response


@csrf_exempt
@require_http_methods(["GET", "PATCH", "DELETE"])
def api_me(request):
    """
    GET /api/identities/me/
    PATCH /api/identities/me/ body: { display_name: str }
    DELETE /api/identities/me/
    """
    if request.method == "GET":
        if request.identity is None:
            return JsonResponse({"identity": None})
        return JsonResponse({"identity": _serialize_identity(request.identity)})

    if request.identity is None:
        return JsonResponse({"error": "Identity required."}, status=401)

    identity = request.identity

    if request.method == "PATCH":
        try:
            body = json.loads(request.body) if request.body else {}
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON body."}, status=400)

        display_name = (body.get("display_name") or "").strip()
        if not display_name:
            return JsonResponse({"error": "display_name is required."}, status=400)
        if len(display_name) > 100:
            return JsonResponse({"error": "display_name is too long."}, status=400)

        identity.display_name = display_name
        identity.save(update_fields=["display_name", "updated_at"])
        return JsonResponse({"identity": _serialize_identity(identity)})

    identity.status = IdentityStatus.DELETED
    identity.save(update_fields=["status", "updated_at"])
    now = timezone.now()
    GuestSession.objects.filter(identity=identity, is_revoked=False).update(
        is_revoked=True,
        revoked_at=now,
    )

    response = JsonResponse({"deleted": True})
    response.delete_cookie(GUEST_SESSION_COOKIE_NAME)
    return response
