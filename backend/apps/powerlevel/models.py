"""Power level — editorial card ratings.

Power level is attached to the **canonical card identity** (not a printing) and
is scoped **per format** (a card can be 8 in Standard and 5 in Premium). ONLY a
Platform Admin may create/edit it, and every change is audited with the previous
value, new value, admin, justification, source and version.
"""
from django.conf import settings
from django.db import models

from apps.common.models import BaseModel


class PowerLevelScale(BaseModel):
    """The configurable rating scale (default 1..10)."""

    name = models.CharField(max_length=80, default="Default 1-10")
    min_value = models.PositiveSmallIntegerField(default=1)
    max_value = models.PositiveSmallIntegerField(default=10)
    # {"1": "very low impact", ... "10": "format-warping"}
    descriptions = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.min_value}-{self.max_value})"


class PowerLevelChangeReason(BaseModel):
    """Reusable, taggable justification categories."""

    code = models.SlugField(max_length=48, unique=True)
    label = models.CharField(max_length=120)

    def __str__(self) -> str:
        return self.label


class CardPowerLevel(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    card = models.ForeignKey("cards.Card", on_delete=models.CASCADE, related_name="power_levels")
    format_code = models.CharField(max_length=32, db_index=True)
    scale = models.ForeignKey(PowerLevelScale, on_delete=models.PROTECT, related_name="+")
    value = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT,
                              db_index=True)
    justification = models.TextField(blank=True)
    confidence = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-5, optional")
    tags = models.JSONField(default=list, blank=True)
    version = models.PositiveIntegerField(default=1)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, related_name="+")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["card", "format_code"], name="uniq_card_format_power")
        ]
        indexes = [models.Index(fields=["format_code", "status"])]

    def __str__(self) -> str:
        return f"{self.card_id} @ {self.format_code}: {self.value} ({self.status})"


class CardPowerLevelHistory(models.Model):
    """Append-only audit of every power level change (spec-mandated fields)."""

    class Source(models.TextChoices):
        ADMIN_SINGLE = "admin_single", "Admin — single edit"
        ADMIN_BULK = "admin_bulk", "Admin — bulk edit"
        IMPORT = "import", "Import"
        AI_SUGGESTION = "ai_suggestion", "AI suggestion (never auto-published)"

    card = models.ForeignKey("cards.Card", on_delete=models.CASCADE, related_name="power_history")
    format_code = models.CharField(max_length=32, db_index=True)
    previous_value = models.SmallIntegerField(null=True, blank=True)
    new_value = models.SmallIntegerField(null=True, blank=True)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                              null=True, related_name="+")
    justification = models.TextField(blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.ADMIN_SINGLE)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["card", "format_code", "created_at"])]

    def __str__(self) -> str:
        return f"{self.card_id} {self.previous_value}→{self.new_value} @ {self.format_code}"


class TournamentPowerPolicy(BaseModel):
    """A reusable power-level policy that a tournament can select. The organizer
    NEVER changes a card's level — only picks constraints over existing levels."""

    class Kind(models.TextChoices):
        NONE = "none", "No power restriction"
        MAX_PER_CARD = "max_per_card", "Max power level per card"
        RANGE = "range", "Allowed range"
        MAX_ABOVE = "max_above", "Max cards above a level"
        POINT_BUDGET = "point_budget", "Total power-point budget"
        MAX_COPIES_ABOVE = "max_copies_above", "Max copies of cards above a level"
        CUSTOM = "custom", "Custom combination"

    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.NONE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                              related_name="+")
    config = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.name} [{self.kind}]"


class TournamentPowerPolicyRule(BaseModel):
    policy = models.ForeignKey(TournamentPowerPolicy, on_delete=models.CASCADE,
                               related_name="rules")
    kind = models.CharField(max_length=20, choices=TournamentPowerPolicy.Kind.choices)
    params = models.JSONField(default=dict, blank=True)
