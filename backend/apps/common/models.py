"""Shared abstract models and the platform-wide audit log."""
import uuid

from django.conf import settings
from django.db import models


class UUIDModel(models.Model):
    """Public identifier is always a UUID; PK stays BigAuto for join speed."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def soft_delete(self):
        from django.utils import timezone

        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])


class BaseModel(UUIDModel, TimeStampedModel):
    class Meta:
        abstract = True


class AuditLog(UUIDModel, models.Model):
    """Append-only record of important platform actions.

    Domain-specific audit tables (power level history, tournament audit) exist
    too; this is the cross-cutting catch-all for administrative actions.
    """

    class Action(models.TextChoices):
        POWER_LEVEL_CHANGE = "power_level_change", "Power level change"
        BANLIST_OFFICIAL_CHANGE = "banlist_official_change", "Official banlist change"
        FORMAT_RULE_CHANGE = "format_rule_change", "Format rule change"
        MATCH_RESULT_CORRECTION = "match_result_correction", "Match result correction"
        DISQUALIFICATION = "disqualification", "Disqualification"
        BRACKET_CHANGE = "bracket_change", "Bracket change"
        DECK_SUBMISSION_CHANGE = "deck_submission_change", "Deck submission change"
        ADMIN_ACTION = "admin_action", "Administrative action"
        DATA_SYNC = "data_sync", "Data synchronization"

    action = models.CharField(max_length=48, choices=Action.choices, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_entries",
    )
    # Generic-ish pointer without contenttypes overhead: model label + object uuid.
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    summary = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=64, blank=True, default="api")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["target_type", "target_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} @ {self.created_at:%Y-%m-%d %H:%M}"


def record_audit(*, action: str, actor=None, target=None, summary="", payload=None,
                 source="api") -> "AuditLog":
    """Helper to append an audit entry from anywhere in the codebase."""
    target_type = ""
    target_id = ""
    if target is not None:
        target_type = target.__class__.__name__
        target_id = str(getattr(target, "uuid", getattr(target, "pk", "")))
    return AuditLog.objects.create(
        action=action,
        actor=actor,
        target_type=target_type,
        target_id=target_id,
        summary=summary[:255],
        payload=payload or {},
        source=source,
    )
