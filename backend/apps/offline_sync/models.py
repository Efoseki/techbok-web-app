import uuid
from django.conf import settings
from django.db import models

class SyncEvent(models.Model):
    """Idempotent receipt for a client operation envelope; domain handlers are added per module."""
    event_id = models.UUIDField(primary_key=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sync_events')
    device_id = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=40)
    operation = models.CharField(max_length=20, default='upsert')
    branch_id = models.PositiveBigIntegerField(null=True, blank=True)
    payload = models.JSONField(default=dict)
    client_created_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=24, default='received')
    result = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['received_at']
        indexes = [models.Index(fields=['user','received_at'], name='offline_sy_user_id_0a41ad_idx'), models.Index(fields=['device_id','received_at'], name='offline_sy_device__e0a5e9_idx')]

    def __str__(self):
        return f'{self.entity_type}:{self.event_id} ({self.status})'
