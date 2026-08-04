"""Idempotent import orchestration.

Running the same import twice produces the same catalog state: sets, cards and
printings are upserted by stable keys, and re-running only updates changed fields.
Every raw record is persisted for auditability before it is transformed.
"""
from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from apps.cards.models import (
    Card,
    CardExternalIdentifier,
    CardFormatLegality,
    CardPriceHistory,
    CardPrinting,
    CardSet,
    normalize_name,
)
from apps.common.models import record_audit

from .adapters.base import CardRecord, SetRecord
from .adapters.registry import get_adapter
from .models import DataSource, ImportBatch, RawImportPayload

logger = logging.getLogger("imports")


class ImportRunner:
    def __init__(self, source: DataSource, *, triggered_by: str = "system"):
        self.source = source
        self.triggered_by = triggered_by
        self.adapter = get_adapter(source.key, {**source.config,
                                                "base_url": source.base_url,
                                                "rate_limit_per_sec": source.rate_limit_per_sec})

    def _new_batch(self, kind: str, incremental: bool) -> ImportBatch:
        return ImportBatch.objects.create(
            source=self.source, kind=kind, is_incremental=incremental,
            status=ImportBatch.Status.RUNNING, started_at=timezone.now(),
            triggered_by=self.triggered_by,
        )

    def _finish(self, batch: ImportBatch, *, failed: bool = False):
        batch.finished_at = timezone.now()
        if failed:
            batch.status = ImportBatch.Status.FAILED
        elif batch.failed and batch.processed:
            batch.status = ImportBatch.Status.PARTIAL
        else:
            batch.status = ImportBatch.Status.SUCCESS
        batch.save()
        record_audit(action="data_sync", summary=f"{batch.kind} import {batch.status}",
                     target=batch, payload=batch.metrics, source="import")

    # -- Sets ---------------------------------------------------------------
    def import_sets(self) -> ImportBatch:
        batch = self._new_batch(ImportBatch.Kind.SETS, incremental=True)
        try:
            records = self.adapter.fetch_sets()
        except Exception as exc:  # noqa: BLE001
            batch.error = str(exc)
            self._finish(batch, failed=True)
            return batch

        for rec in records:
            try:
                self._upsert_set(batch, rec)
            except Exception as exc:  # noqa: BLE001
                batch.failed += 1
                logger.exception("set import failed: %s", exc)
            batch.processed += 1
        self._finish(batch)
        return batch

    def _upsert_set(self, batch: ImportBatch, rec: SetRecord):
        RawImportPayload.objects.create(batch=batch, endpoint="sets",
                                        external_id=rec.external_id, payload=rec.raw)
        obj, created = CardSet.objects.update_or_create(
            external_source=self.source.key, external_id=rec.external_id,
            defaults={"code": rec.code, "name": rec.name, "release_date": rec.release_date},
        )
        batch.created += int(created)
        batch.updated += int(not created)

    # -- Cards + printings --------------------------------------------------
    def import_cards(self, set_external_id: str | None = None) -> ImportBatch:
        batch = self._new_batch(ImportBatch.Kind.PRODUCTS, incremental=set_external_id is not None)
        try:
            records = self.adapter.fetch_cards(set_external_id)
        except Exception as exc:  # noqa: BLE001
            batch.error = str(exc)
            self._finish(batch, failed=True)
            return batch

        for rec in records:
            try:
                with transaction.atomic():
                    self._upsert_card(batch, rec)
            except Exception as exc:  # noqa: BLE001
                batch.failed += 1
                logger.exception("card import failed for %s: %s", rec.external_id, exc)
            batch.processed += 1
        self._finish(batch)
        return batch

    def _resolve_card(self, rec: CardRecord) -> tuple[Card, bool]:
        """Find the canonical identity by external identifier; else by normalized
        name + grade; else create it."""
        for source, identifier in rec.external_identifiers.items():
            existing = CardExternalIdentifier.objects.filter(
                source=source, identifier=identifier
            ).select_related("card").first()
            if existing:
                return existing.card, False

        norm = normalize_name(rec.name)
        card = Card.objects.filter(normalized_name=norm, grade=rec.grade).first()
        if card:
            return card, False

        card = Card.objects.create(
            name=rec.name, grade=rec.grade, power=rec.power, shield=rec.shield,
            critical=rec.critical, card_type=rec.card_type, trigger=rec.trigger,
            nation=rec.nation, clan=rec.clan, race=rec.race, ability_text=rec.ability_text,
            keywords=rec.keywords,
            rules_data={"grade": rec.grade, "trigger": rec.trigger, "card_type": rec.card_type,
                        "critical": rec.critical, "shield": rec.shield},
        )
        return card, True

    def _upsert_card(self, batch: ImportBatch, rec: CardRecord):
        set_obj = CardSet.objects.filter(
            external_source=self.source.key, external_id=rec.set_external_id
        ).first() or CardSet.objects.filter(code=rec.set_external_id).first()
        if not set_obj:
            set_obj = CardSet.objects.create(
                external_source=self.source.key, external_id=rec.set_external_id,
                code=rec.set_external_id, name=rec.set_external_id,
            )

        RawImportPayload.objects.create(batch=batch, endpoint="products",
                                        external_id=rec.external_id, payload=rec.raw)

        card, card_created = self._resolve_card(rec)

        # External identifiers (idempotent)
        for source, identifier in rec.external_identifiers.items():
            CardExternalIdentifier.objects.get_or_create(
                card=card, source=source, identifier=identifier
            )

        # Format legality
        for fmt in rec.formats:
            CardFormatLegality.objects.get_or_create(card=card, format_code=fmt)

        # Printing upsert (stable key: number + set + language + finish)
        printing, printing_created = CardPrinting.objects.update_or_create(
            card_number=rec.card_number, card_set=set_obj,
            language=rec.language, finish=rec.finish,
            defaults={
                "card": card, "rarity": rec.rarity, "illustrator": rec.illustrator,
                "image_url": rec.image_url, "price": rec.price,
                "supplier_product_id": rec.external_id, "data_source": self.source.key,
                "last_synced_at": timezone.now(),
            },
        )
        if rec.price is not None:
            CardPriceHistory.objects.create(printing=printing, price=rec.price,
                                            source=self.source.key)

        if card_created or printing_created:
            batch.created += 1
        else:
            batch.updated += 1

    # -- Prices -------------------------------------------------------------
    def import_prices(self) -> ImportBatch:
        batch = self._new_batch(ImportBatch.Kind.PRICES, incremental=True)
        try:
            records = self.adapter.fetch_prices()
        except Exception as exc:  # noqa: BLE001
            batch.error = str(exc)
            self._finish(batch, failed=True)
            return batch
        for rec in records:
            printing = CardPrinting.objects.filter(
                data_source=self.source.key, supplier_product_id=rec.supplier_product_id
            ).first()
            if not printing:
                batch.skipped += 1
            else:
                printing.price = rec.price
                printing.last_synced_at = timezone.now()
                printing.save(update_fields=["price", "last_synced_at"])
                CardPriceHistory.objects.create(printing=printing, price=rec.price,
                                                currency=rec.currency, source=self.source.key)
                batch.updated += 1
            batch.processed += 1
        self._finish(batch)
        return batch

    def full_sync(self, set_external_id: str | None = None) -> list[ImportBatch]:
        batches = [self.import_sets()]
        adapter_sets = CardSet.objects.filter(external_source=self.source.key)
        if set_external_id:
            batches.append(self.import_cards(set_external_id))
        elif self.source.key == "tcgcsv":
            for s in adapter_sets:
                batches.append(self.import_cards(s.external_id))
        else:
            batches.append(self.import_cards())
        return batches


def ensure_source(key: str, name: str, *, base_url: str = "", config: dict | None = None) -> DataSource:
    source, _ = DataSource.objects.get_or_create(
        key=key, defaults={"name": name, "base_url": base_url, "config": config or {}}
    )
    return source
