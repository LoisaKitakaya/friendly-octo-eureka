from django.contrib import admin
from .models import User, ArtistProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "is_artist", "is_staff", "date_joined")
    list_filter = ("is_artist", "is_staff", "is_superuser", "date_joined")
    search_fields = ("username", "email")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "bio",
                    "profile_picture",
                    "country",
                    "website",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_artist",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )


@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = ("store_name", "user", "slug")
    search_fields = ("store_name", "user__username")
    prepopulated_fields = {"slug": ("store_name",)}
