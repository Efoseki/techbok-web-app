from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone


def branch_centre_code(branch):
    code = str(getattr(branch, "centre_code", "") or "").strip()
    if len(code) != 2 or not code.isdigit():
        raise ValidationError("The selected branch must have a two-digit centre code before records can be numbered.")
    return code


def allocate_student_id(branch, issued_on=None):
    from .models import StudentNumberSequence

    year = (issued_on or timezone.localdate()).year % 100
    centre = branch_centre_code(branch)
    with transaction.atomic():
        sequence, _ = StudentNumberSequence.objects.select_for_update().get_or_create(
            branch=branch, defaults={"last_serial": 0}
        )
        sequence.last_serial += 1
        sequence.save(update_fields=["last_serial"])
        serial = sequence.last_serial
    return f"T{centre}{year:02d}{serial:06d}"


def allocate_course_registration_id(branch, issued_on=None):
    from .models import CourseRegistrationSequence

    issued_on = issued_on or timezone.localdate()
    year = issued_on.year
    centre = branch_centre_code(branch)
    with transaction.atomic():
        sequence, _ = CourseRegistrationSequence.objects.select_for_update().get_or_create(
            branch=branch, year=year, defaults={"last_serial": 0}
        )
        sequence.last_serial += 1
        sequence.save(update_fields=["last_serial"])
        serial = sequence.last_serial
    return f"R{centre}{year % 100:02d}{serial:05d}"
