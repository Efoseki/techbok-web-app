from django.core.exceptions import ValidationError

PASSPORT_MAX_BYTES = 2 * 1024 * 1024
QUALIFICATION_MAX_BYTES = 5 * 1024 * 1024
PASSPORT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
QUALIFICATION_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


def _extension(filename):
    name = (filename or "").lower()
    if "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1]


def validate_passport_photo(file):
    if file.size > PASSPORT_MAX_BYTES:
        raise ValidationError("Passport photographs must be 2 MB or smaller.")
    if _extension(getattr(file, "name", "")) not in PASSPORT_EXTENSIONS:
        raise ValidationError("Upload a JPEG, PNG or WebP passport photograph.")


def validate_qualification_document(file):
    if file.size > QUALIFICATION_MAX_BYTES:
        raise ValidationError("Certificate uploads must be 5 MB or smaller.")
    if _extension(getattr(file, "name", "")) not in QUALIFICATION_EXTENSIONS:
        raise ValidationError("Upload a PDF, JPEG, PNG or WebP certificate.")
