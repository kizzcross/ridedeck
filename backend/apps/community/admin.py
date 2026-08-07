from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("target_type", "target_uuid", "author", "created_at", "deleted_at")
    list_filter = ("target_type",)
    search_fields = ("body", "author__username")
    raw_id_fields = ("author",)
