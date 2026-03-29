import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DomainEventLog",
            fields=[
                ("event_id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(db_index=True, max_length=128)),
                ("room_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("participant_id", models.UUIDField(blank=True, null=True)),
                ("table_id", models.UUIDField(blank=True, null=True)),
                ("match_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("tournament_id", models.UUIDField(blank=True, null=True)),
                ("actor_identity_id", models.UUIDField(blank=True, null=True)),
                ("payload_json", models.JSONField(default=dict)),
                ("occurred_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={"db_table": "domain_event_log", "ordering": ["occurred_at"]},
        ),
        migrations.CreateModel(
            name="AdminAuditLog",
            fields=[
                ("admin_audit_log_id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("admin_actor_id", models.UUIDField()),
                ("action_type", models.CharField(max_length=128)),
                ("target_type", models.CharField(max_length=64)),
                ("target_id", models.UUIDField(blank=True, null=True)),
                ("payload_json", models.JSONField(default=dict)),
                ("occurred_at", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"db_table": "admin_audit_log", "ordering": ["occurred_at"]},
        ),
    ]
