from django.contrib import admin

from .models import TestQuestion, TestOption, TestAttempt, TestAnswer, TopicProgress


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "topic", "order", "is_active", "created_at")
    list_filter = ("topic", "is_active")
    ordering = ("topic", "order")


@admin.register(TestOption)
class TestOptionAdmin(admin.ModelAdmin):
    list_display = ("question", "text", "is_correct")
    list_filter = ("is_correct",)


class TestAnswerInline(admin.TabularInline):
    model = TestAnswer
    extra = 0


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_profile", "topic", "correct_answers", "total_questions", "passed", "created_at")
    list_filter = ("passed", "topic")
    inlines = (TestAnswerInline,)


@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    list_display = ("student_profile", "topic", "best_score", "attempts_count", "is_completed")
