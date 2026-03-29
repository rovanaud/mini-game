import uuid

from django.db import models
from django.utils import timezone


class DomainEventLog(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=128, db_index=True)
    room_id = models.UUIDField(null=True, blank=True, db_index=True)
    participant_id = models.UUIDField(null=True, blank=True)
    table_id = models.UUIDField(null=True, blank=True)
    match_id = models.UUIDField(null=True, blank=True, db_index=True)
    tournament_id = models.UUIDField(null=True, blank=True)
    actor_identity_id = models.UUIDField(null=True, blank=True)
    payload_json = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "domain_event_log"
        ordering = ["occurred_at"]


class AdminAuditLog(models.Model):
    admin_audit_log_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    admin_actor_id = models.UUIDField()
    action_type = models.CharField(max_length=128)
    target_type = models.CharField(max_length=64)
    target_id = models.UUIDField(null=True, blank=True)
    payload_json = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "admin_audit_log"
        ordering = ["occurred_at"]
