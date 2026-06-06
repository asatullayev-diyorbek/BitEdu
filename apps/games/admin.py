from django.contrib import admin

from .models import (
    AnagramGame,
    AnagramWord,
    QuizGame,
    QuizGameQuestion,
    QuizGameOption,
    GameAttempt,
)


class AnagramWordInline(admin.TabularInline):
    model = AnagramWord
    extra = 5


@admin.register(AnagramGame)
class AnagramGameAdmin(admin.ModelAdmin):
    list_display = ("title", "xp", "difficulty", "order", "is_active")
    list_filter = ("difficulty", "is_active")
    search_fields = ("title",)
    ordering = ("order",)
    inlines = (AnagramWordInline,)


class QuizGameOptionInline(admin.TabularInline):
    model = QuizGameOption
    extra = 4


class QuizGameQuestionInline(admin.StackedInline):
    model = QuizGameQuestion
    extra = 1


@admin.register(QuizGameQuestion)
class QuizGameQuestionAdmin(admin.ModelAdmin):
    list_display = ("quiz", "order", "text")
    list_filter = ("quiz__difficulty",)
    inlines = (QuizGameOptionInline,)


@admin.register(QuizGame)
class QuizGameAdmin(admin.ModelAdmin):
    list_display = ("title", "difficulty", "xp", "order", "is_active")
    list_filter = ("difficulty", "is_active")
    search_fields = ("title", "description")
    inlines = (QuizGameQuestionInline,)
    ordering = ("difficulty", "order")


@admin.register(GameAttempt)
class GameAttemptAdmin(admin.ModelAdmin):
    list_display = ("student_profile", "game_type", "is_correct", "points_awarded", "created_at")
    list_filter = ("game_type", "is_correct")
    readonly_fields = ("created_at",)
