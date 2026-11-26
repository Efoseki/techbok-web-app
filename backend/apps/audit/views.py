from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import is_system_admin
from .models import AuditEvent
from .serializers import AuditEventSerializer
class AuditEventViewSet(ReadOnlyModelViewSet):
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated]
    queryset = AuditEvent.objects.select_related("actor", "branch").all()
    def get_queryset(self):
        if not is_system_admin(self.request.user): return AuditEvent.objects.none()
        qs = super().get_queryset()
        action = self.request.query_params.get("action")
        if action: qs = qs.filter(action=action)
        return qs
