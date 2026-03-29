import uuid
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matches", "0004_gamematchseat_enrich"),
    ]

    operations = [
        migrations.CreateModel(
            name="MatchSnapshot",
            fields=[
                (
                    "match_snapshot_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("snapshot_version", models.PositiveBigIntegerField()),
                ("state_json", models.JSONField()),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "game_match",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="snapshots",
                        to="matches.gamematch",
                    ),
                ),
            ],
            options={
                "db_table": "game_match_snapshot",
                "ordering": ["snapshot_version"],
            },
        ),
        migrations.AddConstraint(
            model_name="matchsnapshot",
            constraint=models.UniqueConstraint(
                fields=["game_match", "snapshot_version"],
                name="uq_game_match_snapshot_version",
            ),
        ),
    ]
