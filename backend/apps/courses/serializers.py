from rest_framework import serializers
from .models import Course
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "code", "name", "category", "description", "duration_weeks", "delivery_mode", "tuition_fee", "other_fees", "prerequisites", "certification_title", "status", "created_by", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
