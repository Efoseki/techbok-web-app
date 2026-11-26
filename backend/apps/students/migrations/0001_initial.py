# Initial student, admission and enrollment records for Phase 2A.
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("branches", "0001_initial"),
        ("courses", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Student",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("student_number", models.CharField(blank=True, editable=False, max_length=24, null=True, unique=True)),
                ("first_name", models.CharField(max_length=100)),
                ("middle_name", models.CharField(blank=True, max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                ("gender", models.CharField(blank=True, choices=[("female","Female"),("male","Male")], max_length=16)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("address", models.TextField(blank=True)),
                ("guardian_name", models.CharField(blank=True, max_length=180)),
                ("guardian_phone", models.CharField(blank=True, max_length=32)),
                ("guardian_email", models.EmailField(blank=True, max_length=254)),
                ("emergency_contact_name", models.CharField(blank=True, max_length=180)),
                ("emergency_contact_phone", models.CharField(blank=True, max_length=32)),
                ("status", models.CharField(choices=[("active","Active"),("inactive","Inactive"),("graduated","Graduated"),("withdrawn","Withdrawn")], default="active", max_length=16)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="students", to="branches.branch")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_students", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["last_name","first_name"]},
        ),
        migrations.CreateModel(
            name="Admission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("application_number", models.CharField(blank=True, editable=False, max_length=24, null=True, unique=True)),
                ("intake", models.CharField(blank=True, max_length=100)),
                ("first_name", models.CharField(max_length=100)),
                ("middle_name", models.CharField(blank=True, max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                ("gender", models.CharField(blank=True, choices=[("female","Female"),("male","Male"),("other","Other"),("not_stated","Prefer not to say")], max_length=16)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("address", models.TextField(blank=True)),
                ("guardian_name", models.CharField(blank=True, max_length=180)),
                ("guardian_phone", models.CharField(blank=True, max_length=32)),
                ("guardian_email", models.EmailField(blank=True, max_length=254)),
                ("application_date", models.DateField(default=django.utils.timezone.localdate)),
                ("status", models.CharField(choices=[("submitted","Submitted"),("under_review","Under review"),("accepted","Accepted"),("rejected","Rejected"),("withdrawn","Withdrawn")], default="submitted", max_length=16)),
                ("review_notes", models.TextField(blank=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="admissions", to="branches.branch")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="admissions", to="courses.course")),
                ("converted_student", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="source_admission", to="students.student")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_admissions", to=settings.AUTH_USER_MODEL)),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_admissions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["-application_date","-created_at"]},
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enrollment_number", models.CharField(blank=True, editable=False, max_length=24, null=True, unique=True)),
                ("cohort", models.CharField(blank=True, max_length=100)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("expected_end_date", models.DateField(blank=True, null=True)),
                ("tuition_fee", models.DecimalField(decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("other_fees", models.DecimalField(decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("status", models.CharField(choices=[("pending","Pending"),("active","Active"),("completed","Completed"),("deferred","Deferred"),("withdrawn","Withdrawn")], default="pending", max_length=16)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("branch", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="enrollments", to="branches.branch")),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="enrollments", to="courses.course")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_enrollments", to=settings.AUTH_USER_MODEL)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="enrollments", to="students.student")),
            ],
            options={"ordering":["-created_at"]},
        ),
        migrations.AddIndex(model_name="student", index=models.Index(fields=["branch","status"], name="students_st_branch_8e3d4c_idx")),
        migrations.AddIndex(model_name="student", index=models.Index(fields=["last_name","first_name"], name="students_st_last_na_9e4d02_idx")),
        migrations.AddIndex(model_name="admission", index=models.Index(fields=["branch","status"], name="students_ad_branch_5c4e1a_idx")),
        migrations.AddIndex(model_name="admission", index=models.Index(fields=["application_number"], name="students_ad_applica_5f6b2d_idx")),
        migrations.AddConstraint(model_name="enrollment", constraint=models.UniqueConstraint(fields=("student","course","cohort"), name="unique_student_course_cohort")),
        migrations.AddIndex(model_name="enrollment", index=models.Index(fields=["branch","status"], name="students_en_branch_6f1c2a_idx")),
        migrations.AddIndex(model_name="enrollment", index=models.Index(fields=["student","status"], name="students_en_student_4e2d1b_idx")),
    ]
