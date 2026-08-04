from django.contrib import admin

from .models import Deck, DeckComment, DeckEntry, DeckVersion


class DeckEntryInline(admin.TabularInline):
    model = DeckEntry
    extra = 0
    raw_id_fields = ("card", "preferred_printing")


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "format_code", "visibility", "like_count", "updated_at")
    list_filter = ("format_code", "visibility")
    search_fields = ("title", "owner__username")
    raw_id_fields = ("owner", "forked_from", "cover_printing", "current_version")


@admin.register(DeckVersion)
class DeckVersionAdmin(admin.ModelAdmin):
    list_display = ("deck", "version_number")
    inlines = [DeckEntryInline]


admin.site.register(DeckComment)
