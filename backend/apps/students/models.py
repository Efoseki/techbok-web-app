from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

from .identifiers import allocate_course_registration_id, allocate_student_id
from .validators import validate_passport_photo, validate_qualification_document


def passport_upload_to(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    identity = instance.student_number or "pending"
    return f"students/passports/{identity}.{ext}"


def qualification_upload_to(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "pdf"
    identity = instance.student.student_number if instance.student_id else "pending"
    return f"students/qualifications/{identity}-{instance.pk or 'new'}.{ext}"


class StudentNumberSequence(models.Model):
    branch = models.OneToOneField("branches.Branch", on_delete=models.CASCADE, related_name="student_number_sequence")
    last_serial = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.branch} student serial {self.last_serial}"


class CourseRegistrationSequence(models.Model):
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="course_registration_sequences")
    year = models.PositiveIntegerField()
    last_serial = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["branch", "year"], name="unique_branch_year_registration_serial")]

    def __str__(self):
        return f"{self.branch} {self.year} registration serial {self.last_serial}"


class Student(models.Model):
    class Gender(models.TextChoices):
        FEMALE = "female", "Female"
        MALE = "male", "Male"
        

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        GRADUATED = "graduated", "Graduated"
        WITHDRAWN = "withdrawn", "Withdrawn"

    student_number = models.CharField(max_length=24, unique=True, null=True, blank=True, editable=False)
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="students")
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=16, choices=Gender.choices, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=180, blank=True)
    guardian_phone = models.CharField(max_length=32, blank=True)
    guardian_email = models.EmailField(blank=True)
    emergency_contact_name = models.CharField(max_length=180, blank=True)
    emergency_contact_phone = models.CharField(max_length=32, blank=True)
    passport_photo = models.ImageField(upload_to=passport_upload_to, blank=True, null=True, validators=[validate_passport_photo])
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_students")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [models.Index(fields=["branch", "status"], name="students_st_branch_8e3d4c_idx"),
                   models.Index(fields=["last_name", "first_name"], name="students_st_last_na_9e4d02_idx")]

    def save(self, *args, **kwargs):
        if not self.student_number:
            self.student_number = allocate_student_id(self.branch)
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return " ".join(x for x in [self.first_name, self.middle_name, self.last_name] if x)

    def __str__(self):
        return f"{self.student_number or 'New student'} — {self.full_name}"


class StudentQualification(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="qualifications")
    title = models.CharField(max_length=180)
    institution = models.CharField(max_length=180)
    year_obtained = models.PositiveIntegerField(validators=[MinValueValidator(1950), MaxValueValidator(2100)])
    document = models.FileField(upload_to=qualification_upload_to, blank=True, null=True, validators=[validate_qualification_document])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year_obtained", "title"]

    def __str__(self):
        return f"{self.title} ({self.year_obtained})"


class Admission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    application_number = models.CharField(max_length=24, unique=True, null=True, blank=True, editable=False)
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="admissions")
    course = models.ForeignKey("courses.Course", on_delete=models.PROTECT, related_name="admissions")
    intake = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=16, choices=Student.Gender.choices, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=180, blank=True)
    guardian_phone = models.CharField(max_length=32, blank=True)
    guardian_email = models.EmailField(blank=True)
    application_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED)
    review_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_admissions")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    converted_student = models.OneToOneField(Student, null=True, blank=True, on_delete=models.PROTECT, related_name="source_admission")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_admissions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-application_date", "-created_at"]
        indexes = [models.Index(fields=["branch", "status"], name="students_ad_branch_5c4e1a_idx"),
                   models.Index(fields=["application_number"], name="students_ad_applica_5f6b2d_idx")]

    def save(self, *args, **kwargs):
        if self.application_number:
            return super().save(*args, **kwargs)
        super().save(*args, **kwargs)
        self.application_number = f"APP-{timezone.localdate().year}-{self.pk:06d}"
        super().save(update_fields=["application_number"])

    @property
    def applicant_name(self):
        return " ".join(x for x in [self.first_name, self.middle_name, self.last_name] if x)

    def __str__(self):
        return f"{self.application_number or 'New application'} — {self.applicant_name}"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        DEFERRED = "deferred", "Deferred"
        WITHDRAWN = "withdrawn", "Withdrawn"

    enrollment_number = models.CharField(max_length=24, unique=True, null=True, blank=True, editable=False)
    alternative_registration_id = models.CharField(
        max_length=12, blank=True,
        validators=[RegexValidator(r"^.{0,12}$", "Alternative Course Registration ID is limited to 12 characters.")],
    )
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="enrollments")
    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, related_name="enrollments")
    course = models.ForeignKey("courses.Course", on_delete=models.PROTECT, related_name="enrollments")
    cohort = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    expected_end_date = models.DateField(null=True, blank=True)
    tuition_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    other_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_enrollments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["student", "course", "cohort"], name="unique_student_course_cohort"),
            models.UniqueConstraint(
                fields=["alternative_registration_id"],
                condition=~models.Q(alternative_registration_id=""),
                name="unique_alt_course_registration_id",
            ),
        ]
        indexes = [models.Index(fields=["branch", "status"], name="students_en_branch_6f1c2a_idx"),
                   models.Index(fields=["student", "status"], name="students_en_student_4e2d1b_idx")]

    def save(self, *args, **kwargs):
        if self.student_id and self.branch_id and self.student.branch_id != self.branch_id:
            from django.core.exceptions import ValidationError
            raise ValidationError("The enrollment branch must match the student's registered branch.")
        if not self.enrollment_number:
            self.enrollment_number = allocate_course_registration_id(self.branch)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.enrollment_number or 'New enrollment'} — {self.student}"
