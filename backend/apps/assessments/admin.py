from django.contrib import admin
from .models import Assessment, Question, AssessmentAttempt

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display=('title','course','branch','status','starts_at','ends_at','offline_enabled')
    list_filter=('status','branch','offline_enabled')
    search_fields=('title','course__name')
    inlines=[QuestionInline]

@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display=('assessment','student','attempt_number','status','score','submitted_at')
    list_filter=('status','assessment')
    readonly_fields=('assessment','student','attempt_number','started_at','submitted_at','answers','score','marked_by','marked_at','released_at','version')
