import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        STUDENT = "STUDENT", "Student"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True, null=True, blank=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )

    image = models.ImageField(upload_to='users/', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"

    def get_image(self):
        if self.image:
            return self.image.url
        return None


class StudentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    grade = models.ForeignKey(
        "academic.Grade",
        on_delete=models.PROTECT,
        related_name="students",
    )

    total_points = models.PositiveIntegerField(default=0, db_index=True)

    completed_topics_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["total_points"]),
            models.Index(fields=["grade"]),
        ]

    def __str__(self):
        return f"{self.user.username} - Grade {self.grade.name}"
