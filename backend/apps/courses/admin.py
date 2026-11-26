from django.contrib import admin
from .models import Course
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "status", "delivery_mode", "tuition_fee")
    list_filter = ("status", "delivery_mode", "category")
    search_fields = ("name", "code")
