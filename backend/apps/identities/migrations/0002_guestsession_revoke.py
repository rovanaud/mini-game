
# migration 0002_guestsession_revoke.py
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("identities", "0002_guestsession_revoke")]
    operations = [
        migrations.RemoveField(
            model_name="useridentity",
            name="guest_session_key",
        )
    ]
