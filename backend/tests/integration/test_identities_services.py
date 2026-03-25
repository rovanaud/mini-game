import pytest
from apps.identities.services import (
    create_guest_identity,
    create_guest_session,
    restore_guest_session,
)

pytestmark = pytest.mark.django_db


def test_restore_guest_session_returns_identity_for_valid_token():
    identity = create_guest_identity(display_name="Alice")
    session, raw_token = create_guest_session(identity)

    restored_identity = restore_guest_session(raw_token)

    assert restored_identity is not None
    assert restored_identity.pk == identity.pk


def test_restore_guest_session_returns_none_for_invalid_token():
    restored_identity = restore_guest_session("invalid-token")

    assert restored_identity is None
