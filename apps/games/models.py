import uuid
from django.db import models

from apps.users.models import StudentProfile


class GameDifficulty(models.TextChoices):
    EASY = "EASY", "Oson"
    MEDIUM = "MEDIUM", "O'rta"
    HARD = "HARD", "Qiyin"


# ─────────────────────────── ANAGRAM ───────────────────────────
class AnagramGame(models.Model):
    """
    Anagram o'yini — ketma-ket 5 ta so'zdan iborat.
    Har bir so'z topilgach keyingisiga o'tiladi; barchasi topilsa XP beriladi.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=512, blank=True)
    xp = models.PositiveIntegerField(default=10, help_text="Barcha so'zlar topilgani uchun XP")
    difficulty = models.CharField(
        max_length=10,
        choices=GameDifficulty.choices,
        default=GameDifficulty.EASY,
    )
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title


class AnagramWord(models.Model):
    """Anagram o'yinidagi bitta so'z (yashirin javob hech qachon API'da chiqmaydi)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(
        AnagramGame,
        on_delete=models.CASCADE,
        related_name="words",
    )
    text = models.CharField(max_length=64, help_text="Yashirin so'z (masalan: VARIABLE)")
    hint = models.CharField(max_length=255, blank=True, help_text="Ixtiyoriy ishora")
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        unique_together = ("game", "order")

    def __str__(self):
        return f"{self.game.title} - {self.text}"

    @property
    def letters(self):
        return list(self.text.upper())


# ─────────────────────────── QUIZ ───────────────────────────
class QuizGame(models.Model):
    """Qiyinlik bo'yicha guruhlangan kviz (masalan: "Python O'rta - 5")."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=512, blank=True)
    difficulty = models.CharField(
        max_length=10,
        choices=GameDifficulty.choices,
        default=GameDifficulty.MEDIUM,
        db_index=True,
    )
    xp = models.PositiveIntegerField(default=15)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["difficulty", "order"]

    def __str__(self):
        return f"{self.title} [{self.difficulty}]"


class QuizGameQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        QuizGame,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        unique_together = ("quiz", "order")

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"


class QuizGameOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        QuizGameQuestion,
        on_delete=models.CASCADE,
        related_name="options",
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text[:40]} ({'✓' if self.is_correct else '✗'})"


# ───────────────── O'YIN URINISHLARI (Anagram + Quiz) ─────────────────
class GameAttempt(models.Model):
    """
    Har bir o'yin urinishi shu yerda yoziladi.
    Ball faqat birinchi to'g'ri urinishda beriladi (keyingi safar points_awarded=0).
    """
    class GameType(models.TextChoices):
        ANAGRAM = "ANAGRAM", "Anagram"
        QUIZ = "QUIZ", "Quiz"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_profile = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="game_attempts",
    )
    game_type = models.CharField(
        max_length=10,
        choices=GameType.choices,
        db_index=True,
    )
    anagram = models.ForeignKey(
        AnagramGame,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="attempts",
    )
    quiz = models.ForeignKey(
        QuizGame,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="attempts",
    )
    is_correct = models.BooleanField(default=False)
    points_awarded = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student_profile", "game_type"]),
            models.Index(fields=["student_profile", "anagram"]),
            models.Index(fields=["student_profile", "quiz"]),
        ]

    def __str__(self):
        target = self.anagram or self.quiz
        return f"{self.student_profile} - {target} ({'✓' if self.is_correct else '✗'})"
