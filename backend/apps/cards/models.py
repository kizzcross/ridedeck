"""Card catalog.

The central invariant of the whole platform lives here: a **Card** is the logical
identity (used for copy limits, banlist and power level), while a **CardPrinting**
is a specific physical printing (set, rarity, art, price). Different printings of
the same card are NEVER treated as different cards for gameplay rules.
"""
import re

from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.text import slugify

from apps.common.models import BaseModel, TimeStampedModel

from .choices import (
    CardType,
    EquivalenceStrategy,
    Grade,
    Legality,
    Nation,
    TriggerType,
)


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation/diacritics-ish, collapse whitespace.

    Used for the equivalence strategy 'normalized_name' and for fuzzy search.
    """
    value = name.lower().strip()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


class CardSet(BaseModel):
    # Not unique: real-world data reuses a base code across related products
    # (e.g. multiple "G-LEGEND" decks). Identity is (external_source, external_id).
    code = models.CharField(max_length=32, db_index=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    card_count = models.PositiveIntegerField(default=0)
    external_source = models.CharField(max_length=64, blank=True)
    external_id = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        ordering = ("-release_date", "name")
        indexes = [models.Index(fields=["external_source", "external_id"])]
        constraints = [
            models.UniqueConstraint(
                fields=["external_source", "external_id"],
                name="uniq_set_source_external_id",
                condition=models.Q(external_id__gt=""),
            )
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.code}-{self.name}")[:200] or "set"
            self.slug = f"{base}-{str(self.uuid)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.code} · {self.name}"


class Card(BaseModel):
    """Canonical card identity."""

    name = models.CharField(max_length=255, db_index=True)
    normalized_name = models.CharField(max_length=255, db_index=True, editable=False)
    slug = models.SlugField(max_length=280, unique=True, blank=True)

    ability_text = models.TextField(blank=True)
    flavor_text = models.TextField(blank=True)

    grade = models.PositiveSmallIntegerField(choices=Grade.choices, db_index=True)
    power = models.IntegerField(null=True, blank=True)
    shield = models.IntegerField(null=True, blank=True)
    critical = models.PositiveSmallIntegerField(default=1)

    card_type = models.CharField(max_length=24, choices=CardType.choices, db_index=True)
    trigger = models.CharField(max_length=16, choices=TriggerType.choices, blank=True, default="")

    nation = models.CharField(max_length=32, choices=Nation.choices, blank=True, default="",
                              db_index=True)
    clan = models.CharField(max_length=64, blank=True, default="", db_index=True)
    race = models.CharField(max_length=64, blank=True, default="")

    is_persona_ride = models.BooleanField(default=False)
    keywords = models.JSONField(default=list, blank=True)

    # Normalized data consumed by the rule engine (grade, trigger, counts, flags…).
    rules_data = models.JSONField(default=dict, blank=True)

    equivalence_strategy = models.CharField(
        max_length=32, choices=EquivalenceStrategy.choices,
        default=EquivalenceStrategy.CANONICAL_IDENTITY,
    )

    class Meta:
        ordering = ("name",)
        indexes = [
            models.Index(fields=["grade", "card_type"]),
            models.Index(fields=["nation", "grade"]),
            models.Index(fields=["trigger"]),
            GinIndex(name="card_name_trgm_idx", fields=["name"], opclasses=["gin_trgm_ops"]),
            GinIndex(name="card_ability_trgm_idx", fields=["ability_text"],
                     opclasses=["gin_trgm_ops"]),
        ]

    def save(self, *args, **kwargs):
        self.normalized_name = normalize_name(self.name)
        if not self.slug:
            base = slugify(self.name)[:250] or "card"
            self.slug = f"{base}-{str(self.uuid)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} (G{self.grade})"

    @property
    def is_trigger(self) -> bool:
        return bool(self.trigger)


class CardPrinting(BaseModel):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="printings")
    card_number = models.CharField(max_length=64, db_index=True)
    card_set = models.ForeignKey(CardSet, on_delete=models.PROTECT, related_name="printings")
    rarity = models.CharField(max_length=32, blank=True)
    language = models.CharField(max_length=8, default="en", db_index=True)
    illustrator = models.CharField(max_length=200, blank=True)
    finish = models.CharField(max_length=64, blank=True, help_text="Treatment/finish, e.g. foil")
    image_url = models.URLField(blank=True, max_length=500)
    release_date = models.DateField(null=True, blank=True)

    # Sourcing / sync metadata
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    supplier_product_id = models.CharField(max_length=64, blank=True, db_index=True)
    data_source = models.CharField(max_length=64, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("card_number",)
        constraints = [
            models.UniqueConstraint(
                fields=["card_number", "card_set", "language", "finish"],
                name="uniq_printing_number_set_lang_finish",
            )
        ]
        indexes = [
            models.Index(fields=["card", "language"]),
            models.Index(fields=["data_source", "supplier_product_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.card_number} · {self.card.name}"


class CardImage(TimeStampedModel):
    printing = models.ForeignKey(CardPrinting, on_delete=models.CASCADE, related_name="images")
    url = models.URLField(max_length=500)
    kind = models.CharField(max_length=24, default="full", help_text="full | thumbnail | art")
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.kind} image · {self.printing.card_number}"


class CardExternalIdentifier(TimeStampedModel):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="external_ids")
    source = models.CharField(max_length=64, db_index=True)
    identifier = models.CharField(max_length=128, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "identifier"],
                                    name="uniq_external_identifier")
        ]

    def __str__(self) -> str:
        return f"{self.source}:{self.identifier}"


class CardEquivalenceGroup(BaseModel):
    """Admin-registered set of cards treated as the same identity (e.g. alternate
    names or reprints under a different title)."""

    name = models.CharField(max_length=200)
    reason = models.TextField(blank=True)
    strategy = models.CharField(max_length=32, choices=EquivalenceStrategy.choices,
                                default=EquivalenceStrategy.ADMIN_GROUP)

    def __str__(self) -> str:
        return f"EquivalenceGroup<{self.name}>"


class CardEquivalenceMember(TimeStampedModel):
    group = models.ForeignKey(CardEquivalenceGroup, on_delete=models.CASCADE,
                              related_name="members")
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="equivalence_memberships")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "card"], name="uniq_equivalence_member")
        ]


class CardFormatLegality(TimeStampedModel):
    """Which formats a card can be used in. Uses a format_code string to avoid
    coupling the catalog to the formats app (Phase 5); GameFormat.code matches."""

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="format_legalities")
    format_code = models.CharField(max_length=32, db_index=True)
    legality = models.CharField(max_length=16, choices=Legality.choices, default=Legality.LEGAL)

    class Meta:
        verbose_name_plural = "card format legalities"
        constraints = [
            models.UniqueConstraint(fields=["card", "format_code"], name="uniq_card_format")
        ]

    def __str__(self) -> str:
        return f"{self.card.name} · {self.format_code}: {self.legality}"


class CardPriceHistory(models.Model):
    printing = models.ForeignKey(CardPrinting, on_delete=models.CASCADE, related_name="price_history")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    source = models.CharField(max_length=64, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-recorded_at",)
        indexes = [models.Index(fields=["printing", "recorded_at"])]

    def __str__(self) -> str:
        return f"{self.printing.card_number} @ {self.price} {self.currency}"
