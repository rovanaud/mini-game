
# migration 0002_guestsession_revoke.py
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("identities", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="guestsession",
            name="is_revoked",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="guestsession",
            name="revoked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
