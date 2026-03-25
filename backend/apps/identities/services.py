import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.identities.models import (
    GuestSession,
    IdentityStatus,
    IdentityType,
    UserIdentity,
)

GUEST_SESSION_DURATION_DAYS = 7


def _generate_guest_display_name() -> str:
    suffix = secrets.token_hex(3)
    return f"Guest-{suffix}"


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


@transaction.atomic
def create_guest_identity(display_name: str | None = None) -> UserIdentity:
    identity = UserIdentity.objects.create(
        identity_type=IdentityType.GUEST,
        display_name=display_name or _generate_guest_display_name(),
        status=IdentityStatus.ACTIVE,
    )
    return identity


@transaction.atomic
def create_guest_session(
    identity: UserIdentity,
    *,
    client_fingerprint: str | None = None,
    duration: timedelta | None = None,
) -> tuple[GuestSession, str]:
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    now = timezone.now()
    expires_at = now + (duration or timedelta(days=GUEST_SESSION_DURATION_DAYS))

    session = GuestSession.objects.create(
        identity=identity,
        session_token_hash=token_hash,
        expires_at=expires_at,
        client_fingerprint=client_fingerprint,
    )

    if not identity.guest_session_key:
        identity.guest_session_key = token_hash
        identity.last_seen_at = now
        identity.save(update_fields=["guest_session_key", "last_seen_at", "updated_at"])

    return session, raw_token


@transaction.atomic
def create_guest_identity_and_session(
    *,
    display_name: str | None = None,
    client_fingerprint: str | None = None,
) -> tuple[UserIdentity, GuestSession, str]:
    identity = create_guest_identity(display_name=display_name)
    session, raw_token = create_guest_session(
        identity,
        client_fingerprint=client_fingerprint,
    )
    return identity, session, raw_token


@transaction.atomic
def restore_guest_session(raw_token: str) -> UserIdentity | None:
    token_hash = _hash_token(raw_token)
    now = timezone.now()

    session = (
        GuestSession.objects.select_related("identity")
        .filter(session_token_hash=token_hash, expires_at__gt=now)
        .first()
    )
    if session is None:
        return None

    session.last_seen_at = now
    session.save(update_fields=["last_seen_at"])

    identity = session.identity
    identity.last_seen_at = now
    identity.save(update_fields=["last_seen_at", "updated_at"])

    return identity
