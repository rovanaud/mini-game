
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("identities", "0002_useridentity_remove_guestsessionid")]
    operations = [
        migrations.RemoveField(
            model_name="useridentity",
            name="guest_session_key",
        )
    ]
