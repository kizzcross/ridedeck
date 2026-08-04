from django.contrib import admin

from .models import (
    Banlist,
    BanlistEntry,
    BanlistVersion,
    RestrictionGroup,
    RestrictionGroupMember,
)


class BanlistEntryInline(admin.TabularInline):
    model = BanlistEntry
    extra = 0
    raw_id_fields = ("card", "group")


class GroupMemberInline(admin.TabularInline):
    model = RestrictionGroupMember
    extra = 0
    raw_id_fields = ("card",)


@admin.register(Banlist)
class BanlistAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "format_code", "owner", "like_count", "updated_at")
    list_filter = ("category", "format_code")
    search_fields = ("name",)
    raw_id_fields = ("owner", "forked_from", "current_version")


@admin.register(BanlistVersion)
class BanlistVersionAdmin(admin.ModelAdmin):
    list_display = ("banlist", "version", "status")
    inlines = [BanlistEntryInline]


@admin.register(RestrictionGroup)
class RestrictionGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "limit_value")
    inlines = [GroupMemberInline]
