"""Import & sync layer.

Kept strictly separate from the card domain logic: adapters fetch raw data,
persist the raw payload for auditability, then upsert into the catalog
idempotently. The frontend never talks to external sources — only the backend.
"""
from django.db import models

from apps.common.models import BaseModel


class DataSource(BaseModel):
    """A configured external data provider (an adapter is bound to it by key)."""

    key = models.SlugField(max_length=64, unique=True, help_text="e.g. tcgcsv")
    name = models.CharField(max_length=120)
    base_url = models.URLField(blank=True)
    config = models.JSONField(default=dict, blank=True)
    is_enabled = models.BooleanField(default=True)
    rate_limit_per_sec = models.PositiveIntegerField(default=5)

    def __str__(self) -> str:
        return f"{self.name} ({self.key})"


class ImportBatch(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"

    class Kind(models.TextChoices):
        SETS = "sets", "Sets"
        PRODUCTS = "products", "Products / cards"
        PRICES = "prices", "Prices"
        IMAGES = "images", "Images"
        FULL = "full", "Full sync"

    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name="batches")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING,
                              db_index=True)
    is_incremental = models.BooleanField(default=True)

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Metrics
    processed = models.PositiveIntegerField(default=0)
    created = models.PositiveIntegerField(default=0)
    updated = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)

    log = models.JSONField(default=list, blank=True)
    error = models.TextField(blank=True)
    triggered_by = models.CharField(max_length=64, blank=True, help_text="username or 'system'")

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["source", "kind", "status"])]

    def __str__(self) -> str:
        return f"{self.kind} batch [{self.status}] · {self.source.key}"

    @property
    def metrics(self) -> dict:
        return {
            "processed": self.processed, "created": self.created, "updated": self.updated,
            "skipped": self.skipped, "failed": self.failed,
        }


class RawImportPayload(models.Model):
    """The raw response as received — auditable, replayable, never mutated."""

    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="payloads")
    endpoint = models.CharField(max_length=255, blank=True)
    external_id = models.CharField(max_length=128, blank=True, db_index=True)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["batch", "external_id"])]

    def __str__(self) -> str:
        return f"raw payload {self.external_id or self.pk} · batch {self.batch_id}"
