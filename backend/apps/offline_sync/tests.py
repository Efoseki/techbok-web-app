import uuid
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.accounts.models import BranchMembership
from apps.branches.models import Branch
from apps.courses.models import Course
from apps.students.models import Student
from .models import SyncEvent

User = get_user_model()


class StudentOfflineSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admissions", password="Test-pass-123")
        self.branch = Branch.objects.create(code="benin-city", name="Benin City", centre_code="01")
        BranchMembership.objects.create(user=self.user, branch=self.branch, role="admissions")
        self.course = Course.objects.create(code="python", name="Python Programming", status="active")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.device_id = "test-device-001"

    def event(self, event_id=None):
        return {
            "event_id": str(event_id or uuid.uuid4()),
            "device_id": self.device_id,
            "queued_by": self.user.pk,
            "entity_type": "student_record",
            "operation": "upsert",
            "branch_id": self.branch.pk,
            "payload": {"branch": self.branch.pk, "first_name": "Ada", "last_name": "Okafor", "phone": "08000000000"},
            "created_at": timezone.now().isoformat(),
        }

    def test_offline_student_create_is_applied_and_idempotent(self):
        event = self.event()
        payload = {"device_id": self.device_id, "events": [event]}
        first = self.client.post("/api/sync/batch/", payload, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(len(first.data["acknowledged"]), 1)
        self.assertEqual(Student.objects.count(), 1)
        second = self.client.post("/api/sync/batch/", payload, format="json")
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(second.data["acknowledged"]), 1)
        self.assertEqual(Student.objects.count(), 1)
        sync_event = SyncEvent.objects.get(pk=event["event_id"])
        self.assertEqual(sync_event.status, "processed")

    def test_offline_create_without_branch_write_access_is_rejected(self):
        other = Branch.objects.create(code="auchi", name="Auchi", centre_code="02")
        event = self.event()
        event["branch_id"] = other.pk
        event["payload"]["branch"] = other.pk
        response = self.client.post("/api/sync/batch/", {"device_id":self.device_id,"events":[event]}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["rejected"]), 1)
        self.assertEqual(Student.objects.count(), 0)
