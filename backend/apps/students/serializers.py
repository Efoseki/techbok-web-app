from rest_framework import serializers
from .models import Student, StudentQualification, Admission, Enrollment


class StudentQualificationSerializer(serializers.ModelSerializer):
    document_url = serializers.SerializerMethodField()

    class Meta:
        model = StudentQualification
        fields = ["id", "title", "institution", "year_obtained", "document", "document_url", "created_at", "updated_at"]
        read_only_fields = ["id", "document_url", "created_at", "updated_at"]
        extra_kwargs = {"document": {"write_only": True, "required": False}}

    def get_document_url(self, obj):
        if not obj.document:
            return ""
        request = self.context.get("request")
        url = obj.document.url
        return request.build_absolute_uri(url) if request else url


class StudentSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    branch_centre_code = serializers.CharField(source="branch.centre_code", read_only=True)
    passport_photo_url = serializers.SerializerMethodField()
    qualifications = StudentQualificationSerializer(many=True, read_only=True)

    class Meta:
        model = Student
        fields = ["id", "student_number", "branch", "branch_name", "branch_centre_code", "first_name", "middle_name",
                  "last_name", "full_name", "date_of_birth", "gender", "email", "phone", "address", "guardian_name",
                  "guardian_phone", "guardian_email", "emergency_contact_name", "emergency_contact_phone",
                  "passport_photo", "passport_photo_url", "qualifications", "status", "notes", "created_by",
                  "created_at", "updated_at"]
        read_only_fields = ["id", "student_number", "created_by", "created_at", "updated_at"]
        extra_kwargs = {"passport_photo": {"write_only": True, "required": False}}

    def get_passport_photo_url(self, obj):
        if not obj.passport_photo:
            return ""
        request = self.context.get("request")
        url = obj.passport_photo.url
        return request.build_absolute_uri(url) if request else url


class AdmissionSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.get_full_name", read_only=True)

    class Meta:
        model = Admission
        fields = ["id", "application_number", "branch", "branch_name", "course", "course_name", "intake",
                  "first_name", "middle_name", "last_name", "applicant_name", "date_of_birth", "gender",
                  "email", "phone", "address", "guardian_name", "guardian_phone", "guardian_email",
                  "application_date", "status", "review_notes", "reviewed_by", "reviewed_by_name",
                  "reviewed_at", "converted_student", "created_by", "created_at", "updated_at"]
        read_only_fields = ["id", "application_number", "status", "reviewed_by", "reviewed_at",
                            "converted_student", "created_by", "created_at", "updated_at"]


class EnrollmentSerializer(serializers.ModelSerializer):
    student_number = serializers.CharField(source="student.student_number", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_photo_url = serializers.SerializerMethodField()
    course_name = serializers.CharField(source="course.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = Enrollment
        fields = ["id", "enrollment_number", "alternative_registration_id", "student", "student_number",
                  "student_name", "student_photo_url", "branch", "branch_name", "course", "course_name",
                  "cohort", "start_date", "expected_end_date", "tuition_fee", "other_fees", "status",
                  "notes", "created_by", "created_at", "updated_at"]
        read_only_fields = ["id", "enrollment_number", "created_by", "created_at", "updated_at"]

    def get_student_photo_url(self, obj):
        photo = getattr(obj.student, "passport_photo", None)
        if not photo:
            return ""
        request = self.context.get("request")
        url = photo.url
        return request.build_absolute_uri(url) if request else url

    def validate_alternative_registration_id(self, value):
        value = (value or "").strip()
        if len(value) > 12:
            raise serializers.ValidationError("Alternative Course Registration ID is limited to 12 characters.")
        return value

    def validate(self, attrs):
        student = attrs.get("student", getattr(self.instance, "student", None))
        branch = attrs.get("branch", getattr(self.instance, "branch", None))
        if student and branch and student.branch_id != branch.id:
            raise serializers.ValidationError({"branch": "The enrollment branch must match the student's registered branch."})
        course = attrs.get("course", getattr(self.instance, "course", None))
        cohort = attrs.get("cohort", getattr(self.instance, "cohort", ""))
        if student and course:
            duplicates = Enrollment.objects.filter(student=student, course=course, cohort=cohort)
            if self.instance:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise serializers.ValidationError({"non_field_errors": ["This student is already enrolled in this course and cohort."]})
        alt_id = attrs.get("alternative_registration_id")
        if alt_id:
            clashes = Enrollment.objects.filter(alternative_registration_id=alt_id)
            if self.instance:
                clashes = clashes.exclude(pk=self.instance.pk)
            if clashes.exists():
                raise serializers.ValidationError({"alternative_registration_id": "This alternative registration ID is already in use."})
        return attrs
