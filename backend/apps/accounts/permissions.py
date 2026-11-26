from rest_framework.permissions import BasePermission, SAFE_METHODS

def is_system_admin(user):
    return bool(user and user.is_authenticated and user.is_superuser)

def has_branch_role(user, branch, roles=None):
    if is_system_admin(user): return True
    if not user or not user.is_authenticated or branch is None: return False
    qs = user.branch_memberships.filter(branch=branch, is_active=True)
    if roles: qs = qs.filter(role__in=roles)
    return qs.exists()

class IsSystemAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.method in SAFE_METHODS or is_system_admin(request.user)))
