from datetime import date
from io import BytesIO
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from apps.branches.models import Branch
from apps.courses.models import Course
from .models import Student, Admission, Enrollment, StudentNumberSequence, CourseRegistrationSequence

User = get_user_model()


def tiny_jpeg():
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00" + (b"\x08" * 64) +
        b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
        b"\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08"
        b"\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x7f\xff\xd9"
    )


class StudentAdmissionEnrollmentTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", password="Test-pass-123")
        self.branch = Branch.objects.create(code="benin-city", name="Benin City", centre_code="01")
        self.auchi = Branch.objects.create(code="auchi", name="Auchi", centre_code="02")
        self.course = Course.objects.create(code="python", name="Python Programming", status="active")
        self.client = APIClient()
        self.client.force_authenticate(self.admin)

    def test_student_id_uses_centre_code_year_and_continuous_serial(self):
        year = timezone.localdate().year % 100
        one = Student.objects.create(branch=self.branch, first_name="Ada", last_name="Okafor")
        two = Student.objects.create(branch=self.branch, first_name="John", last_name="Doe")
        auchi_student = Student.objects.create(branch=self.auchi, first_name="Grace", last_name="Ibrahim")
        self.assertEqual(one.student_number, f"T01{year:02d}000001")
        self.assertEqual(two.student_number, f"T01{year:02d}000002")
        self.assertEqual(auchi_student.student_number, f"T02{year:02d}000001")
        self.assertEqual(one.student_number, Student.objects.get(pk=one.pk).student_number)

    def test_student_serial_does_not_reset_in_a_new_year(self):
        Student.objects.create(branch=self.branch, first_name="Ada", last_name="Okafor")
        StudentNumberSequence.objects.filter(branch=self.branch).update(last_serial=12)
        with patch("apps.students.identifiers.timezone") as mocked:
            mocked.localdate.return_value = date(2027, 1, 5)
            next_student = Student.objects.create(branch=self.branch, first_name="Next", last_name="Year")
        self.assertEqual(next_student.student_number, "T0127000013")

    def test_course_registration_id_resets_annually_per_branch(self):
        student = Student.objects.create(branch=self.branch, first_name="Ada", last_name="Okafor")
        other_course = Course.objects.create(code="excel", name="Excel", status="active")
        year = timezone.localdate().year % 100
        first = Enrollment.objects.create(student=student, branch=self.branch, course=self.course, cohort="A")
        second = Enrollment.objects.create(student=student, branch=self.branch, course=other_course, cohort="A")
        self.assertEqual(first.enrollment_number, f"R01{year:02d}00001")
        self.assertEqual(second.enrollment_number, f"R01{year:02d}00002")
        with patch("apps.students.identifiers.timezone") as mocked:
            mocked.localdate.return_value = date(2026, 3, 1)
            auchi_student = Student.objects.create(branch=self.auchi, first_name="Grace", last_name="Ibrahim")
            auchi_reg = Enrollment.objects.create(student=auchi_student, branch=self.auchi, course=self.course, cohort="B")
        self.assertEqual(auchi_reg.enrollment_number, "R022600001")
        with patch("apps.students.identifiers.timezone") as mocked:
            mocked.localdate.return_value = date(2027, 2, 1)
            later = Enrollment.objects.create(student=student, branch=self.branch, course=self.course, cohort="2027")
        self.assertEqual(later.enrollment_number, "R012700001")

    def test_alternative_registration_id_is_optional_and_limited(self):
        student = Student.objects.create(branch=self.branch, first_name="Ada", last_name="Okafor")
        ok = self.client.post("/api/enrollments/", {
            "student": student.pk, "branch": self.branch.pk, "course": self.course.pk,
            "cohort": "Legacy", "alternative_registration_id": "OLD-REG-01",
        }, format="json")
        self.assertEqual(ok.status_code, 201)
        self.assertEqual(ok.data["alternative_registration_id"], "OLD-REG-01")
        too_long = self.client.post("/api/enrollments/", {
            "student": student.pk, "branch": self.branch.pk, "course": self.course.pk,
            "cohort": "TooLong", "alternative_registration_id": "1234567890123",
        }, format="json")
        self.assertEqual(too_long.status_code, 400)

    def test_admission_review_and_conversion_creates_student_and_enrollment(self):
        admission = Admission.objects.create(branch=self.branch, course=self.course, first_name="Ada", last_name="Okafor")
        response = self.client.post(f"/api/admissions/{admission.pk}/review/", {"status":"accepted"}, format="json")
        self.assertEqual(response.status_code, 200)
        response = self.client.post(f"/api/admissions/{admission.pk}/convert/", {}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Enrollment.objects.count(), 1)
        self.assertEqual(Admission.objects.get(pk=admission.pk).converted_student_id, Student.objects.first().pk)
        year = timezone.localdate().year % 100
        self.assertEqual(response.data["student"]["student_number"], f"T01{year:02d}000001")
        self.assertEqual(response.data["enrollment"]["enrollment_number"], f"R01{year:02d}00001")

    def test_duplicate_enrollment_is_rejected(self):
        student = Student.objects.create(branch=self.branch, first_name="Ada", last_name="Okafor")
        Enrollment.objects.create(student=student, branch=self.branch, course=self.course, cohort="Nov 2026")
        response = self.client.post("/api/enrollments/", {
            "student":student.pk,"branch":self.branch.pk,"course":self.course.pk,"cohort":"Nov 2026"
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_branch_membership_limits_student_records(self):
        staff = User.objects.create_user(username="auchi_staff", password="Test-pass-123")
        from apps.accounts.models import BranchMembership
        BranchMembership.objects.create(user=staff, branch=self.auchi, role="admissions")
        Student.objects.create(branch=self.branch, first_name="Hidden", last_name="Student")
        self.client.force_authenticate(staff)
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 0)

    def test_records_cannot_be_deleted(self):
        student = Student.objects.create(branch=self.branch, first_name="Ada", last_name="Okafor")
        response = self.client.delete(f"/api/students/{student.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_passport_photo_and_qualifications(self):
        photo = SimpleUploadedFile("passport.jpg", tiny_jpeg(), content_type="image/jpeg")
        created = self.client.post("/api/students/", {
            "branch": self.branch.pk, "first_name": "Ada", "last_name": "Okafor", "passport_photo": photo,
        }, format="multipart")
        self.assertEqual(created.status_code, 201, created.data)
        self.assertTrue(created.data["passport_photo_url"])
        student_id = created.data["id"]
        document = SimpleUploadedFile("waec.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        qualification = self.client.post(f"/api/students/{student_id}/qualifications/", {
            "title": "WAEC", "institution": "Edo State", "year_obtained": 2020, "document": document,
        }, format="multipart")
        self.assertEqual(qualification.status_code, 201, qualification.data)
        detail = self.client.get(f"/api/students/{student_id}/")
        self.assertEqual(len(detail.data["qualifications"]), 1)
        self.assertEqual(detail.data["qualifications"][0]["title"], "WAEC")
        qual_id = qualification.data["id"]
        deleted = self.client.delete(f"/api/students/{student_id}/qualifications/{qual_id}/")
        self.assertEqual(deleted.status_code, 204)
        self.assertEqual(self.client.get(f"/api/students/{student_id}/").data["qualifications"], [])
