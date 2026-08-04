"""Personal collection.

Ownership is tracked per **printing** (CollectionPrinting), grouped under a
per-identity item (UserCollectionItem) so quantities can be aggregated by the
canonical card. Wishlist and trade offers are separate.

GOLDEN RULE: the collection never blocks adding a card to a deck. Missing copies
are only an indicator (a warning), never a validation error.
"""
from django.conf import settings
from django.db import models

from apps.common.models import BaseModel

from .choices import Condition, WishlistPriority


class UserCollectionItem(BaseModel):
    """One row per (user, card identity) — the container for owned printings and
    identity-level flags."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="collection_items")
    card = models.ForeignKey("cards.Card", on_delete=models.CASCADE, related_name="collected_by")
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "card"], name="uniq_collection_item")
        ]
        indexes = [models.Index(fields=["user", "card"])]

    def owned_quantity(self) -> int:
        return sum(p.quantity for p in self.printings.all())

    def __str__(self) -> str:
        return f"{self.user_id} owns {self.card_id}"


class CollectionPrinting(BaseModel):
    """Owned copies of a specific printing (with condition/finish/language)."""

    item = models.ForeignKey(UserCollectionItem, on_delete=models.CASCADE,
                             related_name="printings")
    printing = models.ForeignKey("cards.CardPrinting", on_delete=models.CASCADE,
                                 related_name="collection_entries")
    quantity = models.PositiveIntegerField(default=1)
    language = models.CharField(max_length=8, default="en")
    condition = models.CharField(max_length=20, choices=Condition.choices,
                                 default=Condition.NEAR_MINT)
    finish = models.CharField(max_length=64, blank=True)
    note = models.CharField(max_length=255, blank=True)
    price_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["item", "printing", "language", "condition", "finish"],
                name="uniq_collection_printing",
            )
        ]

    def __str__(self) -> str:
        return f"{self.quantity}× {self.printing.card_number}"


class WishlistItem(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="wishlist")
    card = models.ForeignKey("cards.Card", on_delete=models.CASCADE, related_name="wishlisted_by")
    priority = models.PositiveSmallIntegerField(choices=WishlistPriority.choices,
                                                default=WishlistPriority.MEDIUM)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-priority", "-created_at")
        constraints = [
            models.UniqueConstraint(fields=["user", "card"], name="uniq_wishlist_item")
        ]


class TradeItem(BaseModel):
    """A printing the user offers for trade."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="trade_items")
    printing = models.ForeignKey("cards.CardPrinting", on_delete=models.CASCADE,
                                 related_name="trade_offers")
    quantity = models.PositiveIntegerField(default=1)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(fields=["user", "printing"], name="uniq_trade_item")
        ]
