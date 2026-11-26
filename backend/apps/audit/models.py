from django.conf import settings
from django.db import models
class AuditEvent(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events")
    action = models.CharField(max_length=100, db_index=True)
    object_type = models.CharField(max_length=100, blank=True, db_index=True)
    object_id = models.CharField(max_length=80, blank=True, db_index=True)
    branch = models.ForeignKey("branches.Branch", null=True, blank=True, on_delete=models.SET_NULL)
    before_data = models.JSONField(default=dict, blank=True)
    after_data = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.created_at} {self.action} {self.object_type}:{self.object_id}"
