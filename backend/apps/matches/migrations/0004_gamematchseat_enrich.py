import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matches", "0003_gamematchseat"),
    ]

    operations = [
        migrations.AddField(
            model_name="gamematchseat",
            name="actor_type",
            field=models.CharField(
                choices=[("human", "Human"), ("bot", "Bot")],
                default="human",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="gamematchseat",
            name="bot_id",
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="gamematchseat",
            name="team_index",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="gamematchseat",
            name="seat_status",
            field=models.CharField(
                choices=[
                    ("reserved", "Reserved"),
                    ("filled", "Filled"),
                    ("vacated", "Vacated"),
                    ("replaced", "Replaced"),
                ],
                default="filled",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="gamematchseat",
            name="joined_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="gamematchseat",
            name="left_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="gamematchseat",
            name="metadata_json",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="gamematchseat",
            name="participant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="game_match_seats",
                to="rooms.participant",
            ),
        ),
    ]
