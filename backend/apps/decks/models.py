"""Decks.

A Deck owns one working DeckVersion (its editable state) plus a history of
versions. DeckEntry references the canonical Card identity (not a printing) —
copy limits, banlist and power level operate on the identity — while carrying a
`preferred_printing` for display. Forks copy the entries; tournament snapshots
(Phase 7) freeze them immutably.
"""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import BaseModel, SoftDeleteModel

from .choices import Visibility, Zone


class DeckTag(BaseModel):
    name = models.CharField(max_length=48, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    def __str__(self) -> str:
        return self.name


class Deck(BaseModel, SoftDeleteModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name="decks")
    title = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    format_code = models.CharField(max_length=32, default="standard", db_index=True)
    visibility = models.CharField(max_length=12, choices=Visibility.choices,
                                  default=Visibility.PRIVATE, db_index=True)

    # Owner-chosen deck strength (1–5). Replaces editorial per-card power level and
    # is the budget unit for Power Pool tournaments. Nullable = not rated yet.
    power_stars = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Força do deck escolhida pelo dono (1–5).",
    )

    nation_focus = models.CharField(max_length=32, blank=True)
    clan_focus = models.CharField(max_length=64, blank=True)
    archetype = models.CharField(max_length=120, blank=True)
    tags = models.ManyToManyField(DeckTag, blank=True, related_name="decks")

    guide = models.TextField(blank=True)
    combos = models.TextField(blank=True)
    matchups = models.TextField(blank=True)
    side_notes = models.TextField(blank=True)
    changelog = models.TextField(blank=True)

    cover_printing = models.ForeignKey("cards.CardPrinting", on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name="+")

    forked_from = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="forks")
    original_author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name="+")

    current_version = models.OneToOneField("DeckVersion", on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name="+")

    like_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["visibility", "format_code"]),
            models.Index(fields=["owner", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} · {self.owner.username}"

    @property
    def is_public(self) -> bool:
        return self.visibility == Visibility.PUBLIC


class DeckVersion(BaseModel):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField(default=1)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("-version_number",)
        constraints = [
            models.UniqueConstraint(fields=["deck", "version_number"],
                                    name="uniq_deck_version_number")
        ]

    def __str__(self) -> str:
        return f"{self.deck.title} v{self.version_number}"

    def zone_counts(self) -> dict:
        counts = {z.value: 0 for z in Zone}
        for entry in self.entries.all():
            counts[entry.zone] = counts.get(entry.zone, 0) + entry.quantity
        return counts


class DeckEntry(BaseModel):
    version = models.ForeignKey(DeckVersion, on_delete=models.CASCADE, related_name="entries")
    card = models.ForeignKey("cards.Card", on_delete=models.PROTECT, related_name="deck_entries")
    preferred_printing = models.ForeignKey("cards.CardPrinting", on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name="+")
    zone = models.CharField(max_length=12, choices=Zone.choices, default=Zone.MAIN_DECK)
    quantity = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ("zone", "card__grade", "card__name")
        constraints = [
            models.UniqueConstraint(fields=["version", "card", "zone"],
                                    name="uniq_entry_version_card_zone"),
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name="entry_qty_positive"),
        ]

    def __str__(self) -> str:
        return f"{self.quantity}× {self.card.name} [{self.zone}]"


class DeckLike(BaseModel):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="deck_likes")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["deck", "user"], name="uniq_deck_like")]


class DeckFavorite(BaseModel):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="favorites")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="deck_favorites")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["deck", "user"], name="uniq_deck_favorite")]


class DeckComment(BaseModel):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="deck_comments")
    body = models.TextField(max_length=2000)

    class Meta:
        ordering = ("created_at",)


class DeckFork(BaseModel):
    """Audit record of a fork (source → copy)."""

    source_deck = models.ForeignKey(Deck, on_delete=models.SET_NULL, null=True,
                                    related_name="fork_records")
    forked_deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="+")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")


class DeckSnapshot(BaseModel):
    """Immutable frozen decklist (used by tournaments in Phase 7)."""

    deck = models.ForeignKey(Deck, on_delete=models.SET_NULL, null=True, related_name="snapshots")
    version_number = models.PositiveIntegerField(default=1)
    payload = models.JSONField(default=dict)
    content_hash = models.CharField(max_length=64, db_index=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name="+")

    def __str__(self) -> str:
        return f"snapshot {self.content_hash[:12]} of {self.deck_id}"
