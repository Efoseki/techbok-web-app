from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator

class Course(models.Model):
    class DeliveryMode(models.TextChoices):
        IN_PERSON = "in_person", "In person"
        ONLINE = "online", "Online"
        HYBRID = "hybrid", "Hybrid"
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=180)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    duration_weeks = models.PositiveSmallIntegerField(null=True, blank=True)
    delivery_mode = models.CharField(max_length=16, choices=DeliveryMode.choices, default=DeliveryMode.IN_PERSON)
    tuition_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    other_fees = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    prerequisites = models.TextField(blank=True)
    certification_title = models.CharField(max_length=180, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_courses")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ["name"]
    def __str__(self): return f"{self.code} — {self.name}"
