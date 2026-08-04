from django.contrib import admin

from .models import (
    Card,
    CardEquivalenceGroup,
    CardEquivalenceMember,
    CardExternalIdentifier,
    CardFormatLegality,
    CardPrinting,
    CardSet,
)


class CardPrintingInline(admin.TabularInline):
    model = CardPrinting
    extra = 0
    fields = ("card_number", "card_set", "rarity", "language", "finish", "price")


class CardFormatLegalityInline(admin.TabularInline):
    model = CardFormatLegality
    extra = 0


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("name", "grade", "card_type", "trigger", "nation", "clan")
    list_filter = ("grade", "card_type", "trigger", "nation")
    search_fields = ("name", "normalized_name", "ability_text")
    inlines = [CardPrintingInline, CardFormatLegalityInline]
    readonly_fields = ("normalized_name", "slug")


@admin.register(CardSet)
class CardSetAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "release_date", "card_count")
    search_fields = ("code", "name")


class CardEquivalenceMemberInline(admin.TabularInline):
    model = CardEquivalenceMember
    extra = 1
    autocomplete_fields = ("card",)


@admin.register(CardEquivalenceGroup)
class CardEquivalenceGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "strategy")
    inlines = [CardEquivalenceMemberInline]


admin.site.register(CardExternalIdentifier)
admin.site.register(CardPrinting)
