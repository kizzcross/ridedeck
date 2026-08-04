"""Banlists.

Three categories (official / community / tournament-custom), each versioned.
Restrictions are modeled as **entities** — never loose strings. Choice
Restriction is a RestrictionGroup with members; conditional rules attach
RestrictionConditions. Only a Platform Admin may mark a banlist official.
"""
from django.conf import settings
from django.db import models

from apps.common.models import BaseModel, SoftDeleteModel

from .choices import (
    BanlistCategory,
    BanlistVersionStatus,
    ConditionType,
    GroupKind,
    RestrictionType,
)


class Banlist(BaseModel, SoftDeleteModel):
    name = models.CharField(max_length=140)
    description = models.TextField(blank=True)
    objective = models.CharField(max_length=255, blank=True)
    format_code = models.CharField(max_length=32, default="standard", db_index=True)
    category = models.CharField(max_length=20, choices=BanlistCategory.choices,
                                default=BanlistCategory.COMMUNITY, db_index=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                              blank=True, related_name="banlists")

    # Community visibility (official is always public).
    is_public = models.BooleanField(default=True)
    is_listed = models.BooleanField(default=True)

    source = models.CharField(max_length=200, blank=True)
    forked_from = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="forks")
    current_version = models.OneToOneField("BanlistVersion", on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name="+")

    like_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [models.Index(fields=["category", "format_code"])]

    def __str__(self) -> str:
        return f"{self.name} [{self.category}]"

    @property
    def is_official(self) -> bool:
        return self.category == BanlistCategory.OFFICIAL


class BanlistVersion(BaseModel):
    banlist = models.ForeignKey(Banlist, on_delete=models.CASCADE, related_name="versions")
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=12, choices=BanlistVersionStatus.choices,
                              default=BanlistVersionStatus.DRAFT, db_index=True)
    effective_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ("-version",)
        constraints = [
            models.UniqueConstraint(fields=["banlist", "version"], name="uniq_banlist_version")
        ]

    def __str__(self) -> str:
        return f"{self.banlist.name} v{self.version}"


class RestrictionGroup(BaseModel):
    """A group of cards for Choice / Max-distinct / Max-total restrictions."""

    version = models.ForeignKey(BanlistVersion, on_delete=models.CASCADE,
                                related_name="restriction_groups")
    name = models.CharField(max_length=140)
    kind = models.CharField(max_length=16, choices=GroupKind.choices, default=GroupKind.CHOICE)
    limit_value = models.PositiveIntegerField(default=1,
                                              help_text="Max distinct/total; for CHOICE = 1")
    note = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"{self.name} [{self.kind}]"


class RestrictionGroupMember(BaseModel):
    group = models.ForeignKey(RestrictionGroup, on_delete=models.CASCADE, related_name="members")
    card = models.ForeignKey("cards.Card", on_delete=models.CASCADE, related_name="+")
    # The chosen card still respects this per-card copy limit.
    per_card_limit = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "card"], name="uniq_group_member")
        ]


class BanlistEntry(BaseModel):
    """A single restriction. References a card (banned/limit/first-vanguard) or a
    group (choice/max-*)."""

    version = models.ForeignKey(BanlistVersion, on_delete=models.CASCADE, related_name="entries")
    restriction_type = models.CharField(max_length=32, choices=RestrictionType.choices)
    card = models.ForeignKey("cards.Card", on_delete=models.CASCADE, null=True, blank=True,
                             related_name="banlist_entries")
    group = models.ForeignKey(RestrictionGroup, on_delete=models.CASCADE, null=True, blank=True,
                              related_name="entries")
    limit_value = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [models.Index(fields=["version", "restriction_type"])]

    def __str__(self) -> str:
        target = self.card_id or (self.group and self.group.name)
        return f"{self.restriction_type}:{target}"

    def effective_limit(self) -> int:
        if self.restriction_type == RestrictionType.LIMIT_TO_1:
            return 1
        if self.restriction_type == RestrictionType.LIMIT_TO_2:
            return 2
        if self.restriction_type == RestrictionType.BANNED:
            return 0
        return self.limit_value if self.limit_value is not None else 0


class RestrictionCondition(BaseModel):
    """Condition that gates a DECK_DEPENDENT_RESTRICTION entry."""

    entry = models.ForeignKey(BanlistEntry, on_delete=models.CASCADE, related_name="conditions")
    condition_type = models.CharField(max_length=16, choices=ConditionType.choices)
    value = models.JSONField(default=dict, blank=True)


# --- Social ---------------------------------------------------------------
class BanlistLike(BaseModel):
    banlist = models.ForeignKey(Banlist, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="banlist_likes")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["banlist", "user"], name="uniq_banlist_like")]


class BanlistFavorite(BaseModel):
    banlist = models.ForeignKey(Banlist, on_delete=models.CASCADE, related_name="favorites")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="banlist_favorites")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["banlist", "user"],
                                               name="uniq_banlist_favorite")]


class BanlistComment(BaseModel):
    banlist = models.ForeignKey(Banlist, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name="banlist_comments")
    body = models.TextField(max_length=2000)

    class Meta:
        ordering = ("created_at",)
