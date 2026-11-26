from django.conf import settings
from django.db import models

class Assessment(models.Model):
    class Status(models.TextChoices):
        DRAFT='draft','Draft'; SCHEDULED='scheduled','Scheduled'; OPEN='open','Open'; CLOSED='closed','Closed'; PUBLISHED='published','Published'
    title = models.CharField(max_length=180)
    course = models.ForeignKey('courses.Course', on_delete=models.PROTECT, related_name='assessments')
    branch = models.ForeignKey('branches.Branch', on_delete=models.PROTECT, related_name='assessments')
    instructions = models.TextField(blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    total_marks = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    pass_mark = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    attempts_allowed = models.PositiveSmallIntegerField(default=1)
    offline_enabled = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_assessments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering=['-created_at']
    def __str__(self): return self.title

class Question(models.Model):
    class Kind(models.TextChoices):
        MCQ='mcq','Multiple choice'; TRUE_FALSE='true_false','True/False'; SHORT='short','Short answer'; ESSAY='essay','Essay'
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='questions')
    prompt = models.TextField()
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.MCQ)
    options = models.JSONField(default=list, blank=True, help_text='For objective questions; keep answer keys server-side.')
    marks = models.DecimalField(max_digits=7, decimal_places=2, default=1)
    position = models.PositiveIntegerField(default=1)
    topic = models.CharField(max_length=120, blank=True)
    difficulty = models.CharField(max_length=20, blank=True)
    # Intentionally not exposed to student serializers; permissions must protect answer keys.
    answer_key = models.JSONField(default=dict, blank=True)
    marking_guide = models.TextField(blank=True)
    class Meta: ordering=['position','id']
    def __str__(self): return f'{self.assessment.title} — Q{self.position}'

class AssessmentAttempt(models.Model):
    class Status(models.TextChoices): IN_PROGRESS='in_progress','In progress'; SUBMITTED='submitted','Submitted'; MARKED='marked','Marked'; RELEASED='released','Released'
    assessment = models.ForeignKey(Assessment, on_delete=models.PROTECT, related_name='attempts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='assessment_attempts')
    attempt_number = models.PositiveSmallIntegerField(default=1)
    started_at = models.DateTimeField()
    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IN_PROGRESS)
    answers = models.JSONField(default=dict, blank=True)
    score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='marked_assessment_attempts')
    marked_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['assessment','student','attempt_number'],name='unique_assessment_student_attempt')]
        ordering=['assessment','student','attempt_number']
    def __str__(self): return f'{self.student} — {self.assessment} (attempt {self.attempt_number})'
