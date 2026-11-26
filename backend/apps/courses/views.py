from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from apps.accounts.permissions import is_system_admin, has_branch_role
from apps.audit.utils import record_audit
from .models import Course
from .serializers import CourseSerializer

EDIT_ROLES = ["branch_manager", "admissions"]
class CourseViewSet(ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]
    queryset = Course.objects.all()
    def get_queryset(self):
        qs = Course.objects.all()
        status = self.request.query_params.get("status")
        if status: qs = qs.filter(status=status)
        search = self.request.query_params.get("search")
        if search: qs = qs.filter(name__icontains=search) | qs.filter(code__icontains=search)
        if self.request.user.is_staff or is_system_admin(self.request.user): return qs.distinct()
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            # Authenticated staff can view catalogue; student-facing APIs should expose active courses only.
            return qs.filter(status=Course.Status.ACTIVE).distinct()
        return qs.none()
    def _can_edit(self):
        user = self.request.user
        return is_system_admin(user) or (user.is_staff and user.branch_memberships.filter(is_active=True, role__in=EDIT_ROLES).exists())
    def perform_create(self, serializer):
        if not self._can_edit(): raise PermissionDenied("You do not have permission to create courses.")
        obj = serializer.save(created_by=self.request.user)
        record_audit(self.request, "course.create", obj, after={"code":obj.code,"name":obj.name,"status":obj.status})
    def perform_update(self, serializer):
        if not self._can_edit(): raise PermissionDenied("You do not have permission to edit courses.")
        before = {"code":serializer.instance.code,"name":serializer.instance.name,"status":serializer.instance.status,"tuition_fee":str(serializer.instance.tuition_fee)}
        obj = serializer.save()
        record_audit(self.request, "course.update", obj, before=before, after={"code":obj.code,"name":obj.name,"status":obj.status,"tuition_fee":str(obj.tuition_fee)})
    def perform_destroy(self, instance):
        if not self._can_edit(): raise PermissionDenied("You do not have permission to archive courses.")
        before = {"status":instance.status}
        instance.status = Course.Status.ARCHIVED
        instance.save(update_fields=["status", "updated_at"])
        record_audit(self.request, "course.archive", instance, before=before, after={"status":instance.status})
