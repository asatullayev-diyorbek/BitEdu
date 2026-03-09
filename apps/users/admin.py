from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import User, StudentProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-date_joined",)

    list_display = (
        "username",
        "email",
        "image_preview",
        "role",
        "is_active",
        "date_joined",
    )

    list_filter = ("role", "is_active")
    search_fields = ("username", "email")
    readonly_fields = (
        "date_joined", "last_login", "updated_at",
        "image_preview"
    )

    fieldsets = (
        (_("Credentials"), {
            "fields": ("username", "password")
        }),
        (_("Personal info"), {
            "fields": ("first_name", "last_name", "email", "image",
                       "image_preview")
        }),
        (_("Role & Status"), {
            "fields": ("role", "is_active")
        }),
        (_("Important dates"), {
            "fields": ("last_login", "date_joined", "updated_at")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "email",
                "role",
                "password1",
                "password2",
                "is_active",
            ),
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;'
                'border-radius:50%;object-fit:cover;" />',
                obj.image.url
            )
        return "-"

    image_preview.short_description = "Image"


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "grade",
        "total_points",
        "completed_topics_count",
        "created_at",
    )
    list_filter = ("grade",)
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")

    autocomplete_fields = ("user", "grade")
