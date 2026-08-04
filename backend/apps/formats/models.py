"""Game formats and their **versioned** rule sets.

Rules live in the database and are versioned with validity dates, so new rule
revisions ship without a code migration. The rule engine (apps.validation) reads
the current FormatRuleVersion for a format at a reference date.
"""
from django.db import models

from apps.common.models import BaseModel


class GameFormat(BaseModel):
    code = models.SlugField(max_length=32, unique=True)   # standard | v_premium | premium | custom
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    is_official = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name

    def current_version(self, at=None):
        from django.utils import timezone

        at = at or timezone.now().date()
        return (
            self.rule_versions.filter(valid_from__lte=at)
            .filter(models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=at))
            .order_by("-valid_from")
            .first()
        )


class FormatRuleVersion(BaseModel):
    game_format = models.ForeignKey(GameFormat, on_delete=models.CASCADE,
                                    related_name="rule_versions")
    version = models.PositiveIntegerField(default=1)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ("-valid_from",)
        constraints = [
            models.UniqueConstraint(fields=["game_format", "version"],
                                    name="uniq_format_version")
        ]

    def __str__(self) -> str:
        return f"{self.game_format.code} rules v{self.version}"


class FormatZoneRule(BaseModel):
    rule_version = models.ForeignKey(FormatRuleVersion, on_delete=models.CASCADE,
                                     related_name="zone_rules")
    zone = models.CharField(max_length=12)  # main_deck | ride_deck | g_deck
    min_count = models.PositiveIntegerField(default=0)
    max_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["rule_version", "zone"], name="uniq_zone_rule")
        ]


class FormatTriggerRule(BaseModel):
    rule_version = models.OneToOneField(FormatRuleVersion, on_delete=models.CASCADE,
                                        related_name="trigger_rule")
    total_triggers = models.PositiveIntegerField(default=16)
    # e.g. {"heal": 4, "over": 1}; absent types are unlimited within total.
    per_type_limits = models.JSONField(default=dict, blank=True)
    over_trigger_limit = models.PositiveIntegerField(default=1)
    # Which zones count toward the trigger total.
    counted_zones = models.JSONField(default=list, blank=True)


class FormatConstructionRule(BaseModel):
    rule_version = models.OneToOneField(FormatRuleVersion, on_delete=models.CASCADE,
                                        related_name="construction_rule")
    copies_per_identity = models.PositiveIntegerField(default=4)
    nation_locked = models.BooleanField(default=True, help_text="Single Nation per deck")
    clan_locked = models.BooleanField(default=False)
    requires_first_vanguard = models.BooleanField(default=False)
    # Free-form extras for special build rules (icons/eras, rideline, etc.).
    extra = models.JSONField(default=dict, blank=True)


class FormatException(BaseModel):
    """Cards allowed by explicit exception in this rule version."""

    rule_version = models.ForeignKey(FormatRuleVersion, on_delete=models.CASCADE,
                                     related_name="exceptions")
    card = models.ForeignKey("cards.Card", on_delete=models.CASCADE, related_name="+")
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["rule_version", "card"], name="uniq_format_exception")
        ]
