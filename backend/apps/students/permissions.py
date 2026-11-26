from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.accounts.permissions import is_system_admin, has_branch_role

EDIT_ROLES = ["branch_manager", "admissions"]
READ_ROLES = ["branch_manager", "admissions", "finance", "instructor", "viewer"]


class HasStudentModuleAccess(BasePermission):
    message = "You do not have permission to access student records in this branch."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if is_system_admin(request.user):
            return True
        branch = getattr(obj, "branch", None)
        roles = READ_ROLES if request.method in SAFE_METHODS else EDIT_ROLES
        return has_branch_role(request.user, branch, roles)


def can_access_branch(user, branch, write=False):
    if is_system_admin(user):
        return True
    roles = EDIT_ROLES if write else READ_ROLES
    return has_branch_role(user, branch, roles)
