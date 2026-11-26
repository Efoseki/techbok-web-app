from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from apps.accounts.permissions import is_system_admin
from apps.audit.utils import record_audit
from apps.courses.models import Course
from apps.branches.models import Branch
from .models import Student, Admission, Enrollment
from .serializers import StudentSerializer, AdmissionSerializer, EnrollmentSerializer, StudentQualificationSerializer
from .permissions import can_access_branch, READ_ROLES


class BranchScopedViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    branch_field = "branch"

    def get_queryset(self):
        qs = self.queryset.select_related("branch")
        if is_system_admin(self.request.user):
            return qs
        branch_ids = self.request.user.branch_memberships.filter(is_active=True, role__in=READ_ROLES).values_list("branch_id", flat=True)
        return qs.filter(branch_id__in=branch_ids)

    def _check_branch(self, branch, write=True):
        if not branch or not can_access_branch(self.request.user, branch, write=write):
            raise PermissionDenied("You do not have the required role for this branch.")

    def perform_destroy(self, instance):
        raise PermissionDenied("Records cannot be permanently deleted. Change their status instead.")


class StudentViewSet(BranchScopedViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related("qualifications")
        status_filter = self.request.query_params.get("status")
        search = self.request.query_params.get("search")
        if status_filter: qs = qs.filter(status=status_filter)
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(student_number__icontains=search) | Q(first_name__icontains=search) |
                           Q(last_name__icontains=search) | Q(email__icontains=search) | Q(phone__icontains=search))
        return qs

    def perform_create(self, serializer):
        branch = serializer.validated_data.get("branch")
        self._check_branch(branch, True)
        obj = serializer.save(created_by=self.request.user)
        record_audit(self.request, "student.create", obj, after={"student_number":obj.student_number,"branch":obj.branch.code})

    def perform_update(self, serializer):
        self._check_branch(serializer.instance.branch, True)
        target_branch = serializer.validated_data.get("branch", serializer.instance.branch)
        self._check_branch(target_branch, True)
        if target_branch.pk != serializer.instance.branch_id and serializer.instance.enrollments.exists():
            raise ValidationError({"branch": "A student with enrollment history cannot be moved to another branch."})
        before = {"status":serializer.instance.status,"email":serializer.instance.email,"phone":serializer.instance.phone}
        obj = serializer.save()
        record_audit(self.request, "student.update", obj, before=before, after={"status":obj.status,"email":obj.email,"phone":obj.phone})

    @action(detail=True, methods=["get", "post"], url_path="qualifications")
    def qualifications(self, request, pk=None):
        student = self.get_object()
        if request.method == "GET":
            serializer = StudentQualificationSerializer(student.qualifications.all(), many=True, context={"request": request})
            return Response(serializer.data)
        self._check_branch(student.branch, True)
        serializer = StudentQualificationSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(student=student)
        record_audit(request, "student.qualification.create", student, after={"qualification": obj.title, "year": obj.year_obtained})
        return Response(StudentQualificationSerializer(obj, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"], url_path=r"qualifications/(?P<qualification_id>[0-9]+)")
    def qualification_item(self, request, pk=None, qualification_id=None):
        student = self.get_object()
        self._check_branch(student.branch, write=request.method != "GET")
        qualification = student.qualifications.filter(pk=qualification_id).first()
        if not qualification:
            raise ValidationError("That qualification was not found on this student record.")
        if request.method == "DELETE":
            title = qualification.title
            qualification.delete()
            record_audit(request, "student.qualification.delete", student, before={"qualification": title})
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = StudentQualificationSerializer(qualification, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        record_audit(request, "student.qualification.update", student, after={"qualification": obj.title, "year": obj.year_obtained})
        return Response(serializer.data)


class AdmissionViewSet(BranchScopedViewSet):
    queryset = Admission.objects.all()
    serializer_class = AdmissionSerializer

    def get_queryset(self):
        qs = super().get_queryset().select_related("course", "reviewed_by", "converted_student")
        status_filter = self.request.query_params.get("status")
        search = self.request.query_params.get("search")
        if status_filter: qs = qs.filter(status=status_filter)
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(application_number__icontains=search) | Q(first_name__icontains=search) |
                           Q(last_name__icontains=search) | Q(email__icontains=search) | Q(phone__icontains=search))
        return qs

    def perform_create(self, serializer):
        branch = serializer.validated_data.get("branch")
        course = serializer.validated_data.get("course")
        self._check_branch(branch, True)
        if not course or course.status != Course.Status.ACTIVE:
            raise ValidationError({"course": "Select an active course."})
        obj = serializer.save(created_by=self.request.user)
        record_audit(self.request, "admission.create", obj, after={"application_number":obj.application_number,"status":obj.status})

    def perform_update(self, serializer):
        self._check_branch(serializer.instance.branch, True)
        if serializer.instance.converted_student_id:
            raise ValidationError("A converted application cannot be edited. Update the student record instead.")
        self._check_branch(serializer.validated_data.get("branch", serializer.instance.branch), True)
        course = serializer.validated_data.get("course")
        if course is not None and course.status != Course.Status.ACTIVE:
            raise ValidationError({"course": "Select an active course."})
        obj = serializer.save()
        record_audit(self.request, "admission.update", obj, after={"application_number":obj.application_number,"status":obj.status})

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        admission = self.get_object()
        self._check_branch(admission.branch, True)
        new_status = request.data.get("status")
        if new_status not in [Admission.Status.UNDER_REVIEW, Admission.Status.ACCEPTED, Admission.Status.REJECTED, Admission.Status.WITHDRAWN]:
            raise ValidationError({"status": "Choose a valid review status."})
        if admission.converted_student_id:
            raise ValidationError("This application has already been converted to a student.")
        before = admission.status
        admission.status = new_status
        admission.review_notes = str(request.data.get("review_notes", admission.review_notes))[:5000]
        admission.reviewed_by = request.user
        admission.reviewed_at = timezone.now()
        admission.save(update_fields=["status","review_notes","reviewed_by","reviewed_at","updated_at"])
        record_audit(request, f"admission.{new_status}", admission, before={"status":before}, after={"status":new_status})
        return Response(self.get_serializer(admission).data)

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        admission = self.get_object()
        self._check_branch(admission.branch, True)
        if admission.status != Admission.Status.ACCEPTED:
            raise ValidationError("Only accepted applications can be converted.")
        if admission.course.status != Course.Status.ACTIVE:
            raise ValidationError("The selected course is no longer active. Update the application before conversion.")
        if admission.converted_student_id:
            raise ValidationError("This application has already been converted.")
        with transaction.atomic():
            student = Student.objects.create(
                branch=admission.branch, first_name=admission.first_name, middle_name=admission.middle_name,
                last_name=admission.last_name, date_of_birth=admission.date_of_birth, gender=admission.gender,
                email=admission.email, phone=admission.phone, address=admission.address,
                guardian_name=admission.guardian_name, guardian_phone=admission.guardian_phone,
                guardian_email=admission.guardian_email, created_by=request.user,
            )
            enrollment = Enrollment.objects.create(
                student=student, branch=admission.branch, course=admission.course, cohort=admission.intake,
                tuition_fee=admission.course.tuition_fee, other_fees=admission.course.other_fees,
                status=Enrollment.Status.PENDING, created_by=request.user,
            )
            admission.converted_student = student
            admission.save(update_fields=["converted_student","updated_at"])
            record_audit(request, "admission.convert", admission, after={"student_number":student.student_number,"enrollment_number":enrollment.enrollment_number})
        return Response({"admission":self.get_serializer(admission).data,
                         "student":StudentSerializer(student).data,
                         "enrollment":EnrollmentSerializer(enrollment).data}, status=status.HTTP_201_CREATED)


class EnrollmentViewSet(BranchScopedViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer

    def get_queryset(self):
        qs = super().get_queryset().select_related("student", "course")
        status_filter = self.request.query_params.get("status")
        search = self.request.query_params.get("search")
        if status_filter: qs = qs.filter(status=status_filter)
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(enrollment_number__icontains=search) | Q(alternative_registration_id__icontains=search) |
                           Q(student__student_number__icontains=search) | Q(student__first_name__icontains=search) |
                           Q(student__last_name__icontains=search) | Q(course__name__icontains=search))
        return qs

    def perform_create(self, serializer):
        student = serializer.validated_data.get("student")
        branch = serializer.validated_data.get("branch")
        course = serializer.validated_data.get("course")
        self._check_branch(branch, True)
        if not student or student.branch_id != branch.id:
            raise ValidationError({"student": "Select a student registered at the selected branch."})
        if not course or course.status != Course.Status.ACTIVE:
            raise ValidationError({"course": "Select an active course."})
        obj = serializer.save(created_by=self.request.user)
        record_audit(self.request, "enrollment.create", obj, after={"enrollment_number":obj.enrollment_number,"student":obj.student.student_number})

    def perform_update(self, serializer):
        self._check_branch(serializer.instance.branch, True)
        branch = serializer.validated_data.get("branch", serializer.instance.branch)
        self._check_branch(branch, True)
        student = serializer.validated_data.get("student", serializer.instance.student)
        if student.branch_id != branch.id:
            raise ValidationError({"branch": "The enrollment branch must match the student's registered branch."})
        course = serializer.validated_data.get("course")
        if course is not None and course.status != Course.Status.ACTIVE:
            raise ValidationError({"course": "Select an active course."})
        obj = serializer.save()
        record_audit(self.request, "enrollment.update", obj, after={"status":obj.status})
