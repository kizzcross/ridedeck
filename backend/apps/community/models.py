"""Community layer: a single generic comment thread usable by any model.

Rather than a dedicated comment table per domain object (decks, banlists,
cards, tournaments, profiles…), a comment carries a ``(target_type,
target_uuid)`` pointer — the same lightweight generic reference the audit log
uses, avoiding Django's contenttypes overhead. Dropping comments onto a new
model is then just adding a ``Target`` choice and pointing the UI at it.
"""
from django.conf import settings
from django.db import models

from apps.common.models import BaseModel, SoftDeleteModel


class Comment(BaseModel, SoftDeleteModel):
    class Target(models.TextChoices):
        DECK = "deck", "Deck"
        BANLIST = "banlist", "Banlist"
        CARD = "card", "Card"
        TOURNAMENT = "tournament", "Tournament"
        PROFILE = "profile", "Profile"

    target_type = models.CharField(max_length=32, choices=Target.choices, db_index=True)
    target_uuid = models.UUIDField(db_index=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_comments",
    )
    body = models.TextField(max_length=2000)

    class Meta:
        ordering = ("created_at",)
        indexes = [models.Index(fields=["target_type", "target_uuid"])]

    def __str__(self):
        return f"{self.target_type}:{self.target_uuid} by {self.author_id}"
