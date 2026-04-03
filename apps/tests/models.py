import uuid
from django.db import models
from django.utils import timezone

from apps.academic.models import Topic
from apps.users.models import StudentProfile


class TestQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="test_questions",
    )
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("topic", "order")

    def __str__(self):
        return f"{self.title} ({self.topic})"


class TestOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        TestQuestion,
        on_delete=models.CASCADE,
        related_name="options",
    )
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Option for {self.question}: {self.text[:40]}"


class TestAttempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="test_attempts",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.PROTECT,
        related_name="test_attempts",
    )
    total_questions = models.PositiveIntegerField()
    correct_answers = models.PositiveIntegerField()
    passed = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student_profile} - {self.topic} ({self.correct_answers}/{self.total_questions})"


class TestAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        TestQuestion,
        on_delete=models.CASCADE,
    )
    selected_option = models.ForeignKey(
        TestOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_correct = models.BooleanField()

    class Meta:
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"Answer {self.question} -> {self.selected_option}"


class TopicProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="topic_progress",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="student_progress",
    )
    best_score = models.PositiveIntegerField(default=0)
    attempts_count = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("student_profile", "topic")

    def __str__(self):
        return f"{self.student_profile} - {self.topic}"

    def mark_attempt(self, score: int, passed: bool):
        self.attempts_count += 1
        self.last_attempt_at = timezone.now()
        self.best_score = max(self.best_score, score)
        if passed:
            self.is_completed = True
        self.save()
