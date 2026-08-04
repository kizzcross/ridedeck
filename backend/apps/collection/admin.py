from django.contrib import admin

from .models import CollectionPrinting, TradeItem, UserCollectionItem, WishlistItem


class CollectionPrintingInline(admin.TabularInline):
    model = CollectionPrinting
    extra = 0
    raw_id_fields = ("printing",)


@admin.register(UserCollectionItem)
class UserCollectionItemAdmin(admin.ModelAdmin):
    list_display = ("user", "card", "owned_quantity")
    search_fields = ("user__username", "card__name")
    raw_id_fields = ("user", "card")
    inlines = [CollectionPrintingInline]


admin.site.register(WishlistItem)
admin.site.register(TradeItem)
