from django.contrib import admin
from .models import AuditEvent
@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "object_type", "object_id", "branch")
    list_filter = ("action", "object_type", "branch", "created_at")
    search_fields = ("actor__username", "object_id", "action")
    readonly_fields = [f.name for f in AuditEvent._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
