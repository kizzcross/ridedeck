from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserPreference, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "username", "role", "is_platform_admin", "is_active", "date_joined")
    list_filter = ("role", "is_active", "is_staff", "email_verified")
    search_fields = ("email", "username")
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Role", {"fields": ("role",)}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser",
                                    "groups", "user_permissions")}),
        ("Meta", {"fields": ("email_verified", "date_joined", "last_login")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",),
                "fields": ("email", "username", "role", "password1", "password2")}),
    )
    readonly_fields = ("date_joined", "last_login")


admin.site.register(UserProfile)
admin.site.register(UserPreference)
