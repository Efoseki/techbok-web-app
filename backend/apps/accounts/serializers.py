from rest_framework import serializers
from .models import User, BranchMembership

class BranchMembershipSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    class Meta:
        model = BranchMembership
        fields = ["id", "branch", "branch_name", "role", "is_active"]

class CurrentUserSerializer(serializers.ModelSerializer):
    memberships = BranchMembershipSerializer(source="branch_memberships", many=True, read_only=True)
    is_system_admin = serializers.BooleanField(source="is_superuser", read_only=True)
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_system_admin", "memberships"]
