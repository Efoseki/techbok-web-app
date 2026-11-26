from django.contrib import admin
from .models import Student, StudentQualification, Admission, Enrollment


class StudentQualificationInline(admin.TabularInline):
    model = StudentQualification
    extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_number", "last_name", "first_name", "branch", "phone", "status")
    list_filter = ("branch", "status", "gender")
    search_fields = ("student_number", "first_name", "last_name", "email", "phone")
    readonly_fields = ("student_number", "created_at", "updated_at")
    inlines = [StudentQualificationInline]


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ("application_number", "last_name", "first_name", "branch", "course", "status", "application_date")
    list_filter = ("branch", "status", "course")
    search_fields = ("application_number", "first_name", "last_name", "email", "phone")
    readonly_fields = ("application_number", "reviewed_by", "reviewed_at", "converted_student", "created_at", "updated_at")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("enrollment_number", "alternative_registration_id", "student", "course", "branch", "cohort", "status")
    list_filter = ("branch", "status", "course")
    search_fields = ("enrollment_number", "alternative_registration_id", "student__student_number", "student__first_name", "student__last_name")
    readonly_fields = ("enrollment_number", "created_at", "updated_at")
