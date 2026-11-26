import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="SyncEvent",
            fields=[
                ("event_id", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("device_id", models.CharField(max_length=80)),
                ("entity_type", models.CharField(max_length=40)),
                ("operation", models.CharField(default="upsert", max_length=20)),
                ("branch_id", models.PositiveBigIntegerField(blank=True, null=True)),
                ("payload", models.JSONField(default=dict)),
                ("client_created_at", models.DateTimeField()),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("status", models.CharField(default="received", max_length=24)),
                ("result", models.JSONField(blank=True, default=dict)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sync_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["received_at"]},
        ),
        migrations.AddIndex(model_name="syncevent", index=models.Index(fields=["user","received_at"], name="offline_sy_user_id_0a41ad_idx")),
        migrations.AddIndex(model_name="syncevent", index=models.Index(fields=["device_id","received_at"], name="offline_sy_device__e0a5e9_idx")),
    ]
