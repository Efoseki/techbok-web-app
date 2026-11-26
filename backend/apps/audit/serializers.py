from rest_framework import serializers
from .models import AuditEvent
class AuditEventSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    class Meta:
        model = AuditEvent
        fields = ["id", "actor", "actor_username", "action", "object_type", "object_id", "branch", "branch_name", "before_data", "after_data", "ip_address", "user_agent", "created_at"]
