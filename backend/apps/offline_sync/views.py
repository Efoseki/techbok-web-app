from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.audit.utils import record_audit
from apps.branches.models import Branch
from apps.courses.models import Course
from apps.students.models import Student, Admission, Enrollment
from apps.students.serializers import StudentSerializer, AdmissionSerializer, EnrollmentSerializer
from apps.students.permissions import can_access_branch
from .models import SyncEvent
from .serializers import SyncBatchSerializer


def process_student_domain_event(request, item):
    """Apply an offline create operation to its official module table."""
    entity = item["entity_type"]
    payload = dict(item["payload"])
    branch_id = item.get("branch_id")
    if not branch_id:
        raise ValidationError({"branch_id": "A branch is required for this record."})
    try:
        branch = Branch.objects.get(pk=branch_id, is_active=True)
    except Branch.DoesNotExist:
        raise ValidationError({"branch_id": "The selected branch is unavailable."})
    if not can_access_branch(request.user, branch, write=True):
        raise PermissionDenied("You no longer have write access to this branch.")
    supplied_branch = payload.get("branch")
    if supplied_branch is not None and str(supplied_branch) != str(branch.pk):
        raise ValidationError({"branch": "The payload branch does not match the sync envelope."})
    payload["branch"] = branch.pk

    if item["operation"] != "upsert":
        raise ValidationError("Offline student, admission and enrollment records support create operations only.")

    if entity == "student_record":
        serializer = StudentSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(created_by=request.user)
        record_audit(request, "student.create.offline", obj,
                     after={"student_number": obj.student_number, "branch": branch.code})
        return {"record_type": "student", "record_id": obj.pk, "reference": obj.student_number}

    if entity == "admission_application":
        course_id = payload.get("course")
        course = Course.objects.filter(pk=course_id, status=Course.Status.ACTIVE).first()
        if not course:
            raise ValidationError({"course": "Select an active course before synchronising this application."})
        serializer = AdmissionSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(created_by=request.user)
        record_audit(request, "admission.create.offline", obj,
                     after={"application_number": obj.application_number, "status": obj.status})
        return {"record_type": "admission", "record_id": obj.pk, "reference": obj.application_number}

    if entity == "enrollment_record":
        course_id = payload.get("course")
        course = Course.objects.filter(pk=course_id, status=Course.Status.ACTIVE).first()
        if not course:
            raise ValidationError({"course": "Select an active course before synchronising this enrollment."})
        serializer = EnrollmentSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        student = serializer.validated_data["student"]
        if student.branch_id != branch.pk:
            raise ValidationError({"student": "The student does not belong to the selected branch."})
        obj = serializer.save(created_by=request.user)
        record_audit(request, "enrollment.create.offline", obj,
                     after={"enrollment_number": obj.enrollment_number, "student": obj.student.student_number})
        return {"record_type": "enrollment", "record_id": obj.pk, "reference": obj.enrollment_number}

    return None


class SyncBatchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SyncBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device_id = serializer.validated_data["device_id"]
        acknowledged, rejected = [], []
        domain_types = {"student_record", "admission_application", "enrollment_record"}

        for item in serializer.validated_data["events"]:
            if item["device_id"] != device_id:
                rejected.append({"event_id": str(item["event_id"]), "reason": "Device ID does not match batch."})
                continue
            if item["entity_type"] in domain_types and item.get("queued_by") != request.user.id:
                rejected.append({"event_id": str(item["event_id"]), "reason": "This offline record was captured under a different staff account. Sign in with the original account to synchronise it."})
                continue
            event_id = item["event_id"]
            existing = SyncEvent.objects.filter(pk=event_id).first()
            if existing:
                if existing.user_id == request.user.id and existing.device_id == device_id:
                    if existing.status == "rejected":
                        rejected.append({"event_id": str(event_id), "reason": existing.result.get("error", "This operation was rejected.")})
                    else:
                        acknowledged.append(str(event_id))
                else:
                    rejected.append({"event_id": str(event_id), "reason": "Event identifier already belongs to another user/device."})
                continue

            event_status = "received"
            result = {"note": "Envelope received; no domain handler is registered for this event type."}
            try:
                with transaction.atomic():
                    if item["entity_type"] in domain_types:
                        result = process_student_domain_event(request, item)
                        event_status = "processed"
                    SyncEvent.objects.create(
                        event_id=event_id, user=request.user, device_id=device_id,
                        entity_type=item["entity_type"], operation=item["operation"],
                        branch_id=item.get("branch_id"), payload=item["payload"],
                        client_created_at=item["created_at"], status=event_status, result=result or {},
                    )
                acknowledged.append(str(event_id))
            except (ValidationError, PermissionDenied, IntegrityError, ObjectDoesNotExist) as exc:
                if hasattr(exc, "detail"):
                    detail = exc.detail
                    reason = str(detail)
                else:
                    reason = str(exc) or "The record conflicts with existing data."
                SyncEvent.objects.create(
                    event_id=event_id, user=request.user, device_id=device_id,
                    entity_type=item["entity_type"], operation=item["operation"],
                    branch_id=item.get("branch_id"), payload=item["payload"],
                    client_created_at=item["created_at"], status="rejected", result={"error": reason},
                )
                rejected.append({"event_id": str(event_id), "reason": reason})

        return Response({
            "acknowledged": acknowledged, "rejected": rejected,
            "received": len(acknowledged), "processing_mode": "domain_aware",
        }, status=status.HTTP_200_OK)
