import uuid
from django.db import models


class Grade(models.Model):
    """
    7-11 sinflar
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=10,
        unique=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subject(models.Model):
    """
    Fan modeli
    Masalan:
    7-sinf Informatika
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=255)

    grade = models.ForeignKey(
        Grade,
        on_delete=models.PROTECT,
        related_name="subjects"
    )

    description = models.TextField(blank=True)

    book_file = models.FileField(
        upload_to="books/",
        null=True,
        blank=True
    )

    book_pages = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Kitob sahifalari soni"
    )

    image = models.ImageField(
        upload_to="subjects/",
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("name", "grade")

    def __str__(self):
        return f"{self.name} ({self.grade})"


class Topic(models.Model):
    """
    Fan ichidagi mavzular
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="topics"
    )

    title = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    video_url = models.URLField(
        blank=True,
        null=True
    )

    order = models.PositiveIntegerField(
        default=1,
        help_text="Mavzu tartibi"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("subject", "order")

    def __str__(self):
        return self.title


class TopicResource(models.Model):
    """
    Mavzuga oid qo'shimcha materiallar: PDF, Link, Taqdimot va h.k.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="resources"
    )
    title = models.CharField(max_length=255, help_text="Material nomi (masalan: Formula list)")
    description = models.TextField(blank=True, help_text="Qisqacha izoh")
    
    # Ham fayl, ham link bo'lishi mumkin
    file = models.FileField(upload_to="topic_resources/", null=True, blank=True)
    url = models.URLField(null=True, blank=True, help_text="Tashqi havola (YouTube, Wikipedia va h.k.)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.title} ({self.topic.title})"