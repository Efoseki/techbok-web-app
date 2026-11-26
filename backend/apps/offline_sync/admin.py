from django.contrib import admin
from .models import SyncEvent

@admin.register(SyncEvent)
class SyncEventAdmin(admin.ModelAdmin):
    list_display = ('event_id','user','device_id','entity_type','status','received_at')
    list_filter = ('entity_type','status','received_at')
    search_fields = ('event_id','user__username','device_id')
    readonly_fields = ('event_id','user','device_id','entity_type','operation','branch_id','payload','client_created_at','received_at','status','result')
