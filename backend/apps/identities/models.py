import uuid

from django.db import models


class IdentityType(models.TextChoices):
    GUEST = "guest", "Guest"
    REGISTERED = "registered", "Registered"


class IdentityStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    DELETED = "deleted", "Deleted"
    MERGED = "merged", "Merged"


class UserIdentity(models.Model):
    identity_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identity_type = models.CharField(max_length=32, choices=IdentityType.choices)
    display_name = models.CharField(max_length=100)
    avatar_url = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=32, choices=IdentityStatus.choices, default=IdentityStatus.ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateTimeField(auto_now_add=True)
    metadata_json = models.JSONField(default=dict)

    class Meta:
        db_table = "user_identity"


class GuestSession(models.Model):
    guest_session_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    identity = models.ForeignKey(
        UserIdentity, on_delete=models.CASCADE, related_name="guest_sessions"
    )
    session_token_hash = models.CharField(max_length=255, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_seen_at = models.DateTimeField(auto_now_add=True)
    client_fingerprint = models.CharField(max_length=255, null=True, blank=True)
    metadata_json = models.JSONField(default=dict)
    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "guest_session"
