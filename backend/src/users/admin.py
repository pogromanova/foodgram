from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count

from .models import User, Subscription


class AvatarInline(admin.StackedInline):
    model = User
    fields = ("avatar",)
    extra = 0
    can_delete = False
    verbose_name = "Аватар"
    verbose_name_plural = "Аватар"
    readonly_fields = ("avatar",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "id",
        "avatar_thumb",
        "username",
        "email",
        "first_name",
        "last_name",
        "subscriptions_count",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )
    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )
    ordering = ("-date_joined",)
    readonly_fields = ("avatar_thumb",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "password",
                    "avatar",
                    "avatar_thumb",
                )
            },
        ),
        (
            "Персональная информация",
            {"fields": ("first_name", "last_name", "email")},
        ),
        (
            "Права доступа",
            {"fields": ("is_active", "is_staff", "is_superuser",
                        "groups", "user_permissions")},
        ),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    @admin.display(description="Аватар")
    def avatar_thumb(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="height:40px; border-radius:50%;" />', obj.avatar.url)
        return "—"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(subs_total=Count("subscribers"))

    @admin.display(description="Подписчики")
    def subscriptions_count(self, obj):
        return obj.subs_total


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    list_filter = ("user", "author")
    search_fields = ("user__username", "author__username")
    autocomplete_fields = ("user", "author")
    actions = ["export_subscriptions_csv"]

    @admin.action(description="Экспортировать выбранные подписки в CSV")
    def export_subscriptions_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=subscriptions.csv"
        writer = csv.writer(response)
        writer.writerow(["id", "user", "author"])

        for sub in queryset.select_related("user", "author"):
            writer.writerow([sub.id, sub.user.username, sub.author.username])
        return response
