from django.core.validators import RegexValidator
from django.db import models


class Branch(models.Model):
    code = models.SlugField(max_length=24, unique=True)
    centre_code = models.CharField(
        max_length=2,
        unique=True,
        validators=[RegexValidator(r"^\d{2}$", "Enter a two-digit centre code, for example 01.")],
        help_text="Two-digit centre code used in Student IDs and Course Registration IDs.",
        default="00",
    )
    name = models.CharField(max_length=120)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
