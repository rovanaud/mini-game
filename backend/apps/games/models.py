from django.db import models


class GameDefinition(models.Model):
    game_key = models.CharField(primary_key=True, max_length=64)
    display_name = models.CharField(max_length=100)
    version = models.CharField(max_length=32)
    category = models.CharField(max_length=64)
    min_players = models.PositiveIntegerField()
    max_players = models.PositiveIntegerField()
    supports_spectators = models.BooleanField(default=True)
    supports_pause = models.BooleanField(default=False)
    supports_resume = models.BooleanField(default=False)
    supports_bots = models.BooleanField(default=False)
    supports_tournament = models.BooleanField(default=False)
    supports_save_resume = models.BooleanField(default=False)
    parameter_schema_json = models.JSONField(default=dict)
    communication_policy_schema_json = models.JSONField(default=dict)
    metadata_json = models.JSONField(default=dict)

    class Meta:
        db_table = "game_definition"
