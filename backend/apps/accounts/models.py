from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models

class CaseInsensitiveUserManager(DjangoUserManager):
    def get_by_natural_key(self, username):
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})
    def _create_user(self, username, email, password, **extra_fields):
        username = (username or "").strip().lower()
        return super()._create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(blank=True)
    objects = CaseInsensitiveUserManager()
    def save(self, *args, **kwargs):
        self.username = self.username.strip().lower()
        super().save(*args, **kwargs)
    def __str__(self):
        return self.get_full_name() or self.username

class BranchMembership(models.Model):
    class Role(models.TextChoices):
        BRANCH_MANAGER = "branch_manager", "Branch Manager"
        FINANCE = "finance", "Finance Officer"
        ADMISSIONS = "admissions", "Admissions Officer"
        INSTRUCTOR = "instructor", "Instructor"
        STUDENT = "student", "Student"
        VIEWER = "viewer", "Read-only Staff"
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="branch_memberships")
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=32, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "branch", "role"], name="unique_user_branch_role")]
        ordering = ["branch__name", "user__username"]
    def __str__(self): return f"{self.user} — {self.branch} ({self.role})"
