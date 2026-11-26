from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import is_system_admin, has_branch_role
from apps.audit.utils import record_audit
from .models import Branch
from .serializers import BranchSerializer

class BranchViewSet(ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        qs = Branch.objects.all()
        if is_system_admin(self.request.user): return qs
        return qs.filter(memberships__user=self.request.user, memberships__is_active=True).distinct()
    def perform_create(self, serializer):
        if not is_system_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only a system administrator can create branches.")
        obj = serializer.save()
        record_audit(self.request, "branch.create", obj, after={"code":obj.code,"name":obj.name})
    def perform_update(self, serializer):
        if not is_system_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only a system administrator can edit branch settings.")
        before = {"code":serializer.instance.code,"name":serializer.instance.name,"is_active":serializer.instance.is_active}
        obj = serializer.save()
        record_audit(self.request, "branch.update", obj, before=before, after={"code":obj.code,"name":obj.name,"is_active":obj.is_active})
    def perform_destroy(self, instance):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Branches cannot be deleted through the API; deactivate them instead.")
