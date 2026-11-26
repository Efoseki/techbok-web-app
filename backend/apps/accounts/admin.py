from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, BranchMembership
admin.site.register(User, UserAdmin)
@admin.register(BranchMembership)
class BranchMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "branch", "role", "is_active")
    list_filter = ("branch", "role", "is_active")
    search_fields = ("user__username", "user__email", "branch__name")
