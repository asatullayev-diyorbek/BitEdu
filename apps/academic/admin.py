from django.contrib import admin
from django.utils.html import format_html
from .models import Grade, Subject, Topic


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "created_at",
    )

    search_fields = (
        "name",
    )

    ordering = (
        "name",
    )

    readonly_fields = (
        "created_at",
    )


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    fields = (
        "title",
        "order",
        "is_active",
    )
    ordering = ("order",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "grade",
        "book_pages",
        "book_preview",
        "created_at",
    )

    list_filter = (
        "grade",
    )

    search_fields = (
        "name",
    )

    inlines = [TopicInline]

    readonly_fields = (
        "created_at",
        "book_preview",
    )

    fieldsets = (
        (
            "Asosiy ma'lumotlar",
            {
                "fields": (
                    "name",
                    "grade",
                    "description",
                )
            },
        ),
        (
            "Kitob",
            {
                "fields": (
                    "book_file",
                    "book_pages",
                    "book_preview",
                )
            },
        ),
        (
            "System",
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )

    def book_preview(self, obj):
        if obj.book_file:
            return format_html(
                '<a href="{}" target="_blank">PDF ochish</a>',
                obj.book_file.url
            )
        return "-"

    book_preview.short_description = "Kitob preview"


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "subject",
        "order",
        "is_active",
        "created_at",
    )

    list_filter = (
        "subject",
        "is_active",
    )

    search_fields = (
        "title",
        "subject__name",
    )

    ordering = (
        "subject",
        "order",
    )

    readonly_fields = (
        "created_at",
    )

    fieldsets = (
        (
            "Mavzu",
            {
                "fields": (
                    "subject",
                    "title",
                    "description",
                    "video_url",
                )
            },
        ),
        (
            "Tartib",
            {
                "fields": (
                    "order",
                    "is_active",
                )
            },
        ),
        (
            "System",
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )
    