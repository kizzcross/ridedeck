"""Deck mutation + basic validation.

The authoritative multi-rule engine lands in Phase 5 (apps.validation); this
module provides the working-version plumbing and a *basic* validator (zone
counts, copy limit, trigger count) using placeholder Standard rules so the
builder has real feedback today.
"""
from __future__ import annotations

import hashlib
import json

from django.db import transaction

from apps.cards.models import Card, CardPrinting

from .choices import Zone
from .models import Deck, DeckEntry, DeckFork, DeckVersion

# Placeholder Standard-format rules (replaced by DB-driven FormatRuleVersion in Phase 5).
BASIC_FORMAT_RULES = {
    "standard": {
        "main_deck": {"min": 50, "max": 50},
        "ride_deck": {"min": 5, "max": 5},
        "g_deck": {"min": 0, "max": 16},
        "trigger_count": 16,
        "copies_per_identity": 4,
    },
    "v_premium": {
        "main_deck": {"min": 50, "max": 50},
        "ride_deck": {"min": 0, "max": 0},
        "g_deck": {"min": 0, "max": 16},
        "trigger_count": 16,
        "copies_per_identity": 4,
    },
    "premium": {
        "main_deck": {"min": 50, "max": 50},
        "ride_deck": {"min": 0, "max": 0},
        "g_deck": {"min": 0, "max": 16},
        "trigger_count": 16,
        "copies_per_identity": 4,
    },
}


@transaction.atomic
def ensure_working_version(deck: Deck) -> DeckVersion:
    if deck.current_version_id:
        return deck.current_version
    version = DeckVersion.objects.create(deck=deck, version_number=1)
    deck.current_version = version
    deck.save(update_fields=["current_version"])
    return version


@transaction.atomic
def set_entry(version: DeckVersion, card: Card, zone: str, quantity: int,
              preferred_printing: CardPrinting | None = None) -> DeckEntry | None:
    """Upsert an entry. quantity<=0 removes it. Returns the entry or None."""
    if quantity <= 0:
        DeckEntry.objects.filter(version=version, card=card, zone=zone).delete()
        return None
    entry, _ = DeckEntry.objects.update_or_create(
        version=version, card=card, zone=zone,
        defaults={"quantity": quantity, "preferred_printing": preferred_printing},
    )
    return entry


@transaction.atomic
def fork_deck(deck: Deck, user) -> Deck:
    source_version = ensure_working_version(deck)
    new_deck = Deck.objects.create(
        owner=user,
        title=f"{deck.title} (fork)",
        description=deck.description,
        format_code=deck.format_code,
        nation_focus=deck.nation_focus,
        clan_focus=deck.clan_focus,
        archetype=deck.archetype,
        forked_from=deck,
        original_author=deck.original_author or deck.owner,
        cover_printing=deck.cover_printing,
    )
    version = DeckVersion.objects.create(deck=new_deck, version_number=1)
    new_deck.current_version = version
    new_deck.save(update_fields=["current_version"])
    entries = [
        DeckEntry(version=version, card=e.card, preferred_printing=e.preferred_printing,
                  zone=e.zone, quantity=e.quantity)
        for e in source_version.entries.all()
    ]
    DeckEntry.objects.bulk_create(entries)
    DeckFork.objects.create(source_deck=deck, forked_deck=new_deck, user=user)
    return new_deck


def _serialize_entries(version: DeckVersion) -> list[dict]:
    return sorted(
        [
            {"card_uuid": str(e.card.uuid), "zone": e.zone, "quantity": e.quantity}
            for e in version.entries.select_related("card")
        ],
        key=lambda x: (x["zone"], x["card_uuid"]),
    )


def snapshot_hash(version: DeckVersion) -> str:
    payload = json.dumps(_serialize_entries(version), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def basic_validate(version: DeckVersion) -> dict:
    """Basic, non-authoritative validation. Full engine = Phase 5."""
    deck = version.deck
    rules = BASIC_FORMAT_RULES.get(deck.format_code, BASIC_FORMAT_RULES["standard"])
    entries = list(version.entries.select_related("card"))

    counts = {z.value: 0 for z in Zone}
    trigger_count = 0
    per_identity: dict[str, int] = {}
    for e in entries:
        counts[e.zone] += e.quantity
        if e.card.trigger:
            trigger_count += e.quantity
        per_identity[str(e.card.uuid)] = per_identity.get(str(e.card.uuid), 0) + e.quantity

    errors, warnings = [], []

    def check_zone(zone_key, label):
        cfg = rules[zone_key]
        n = counts[getattr(Zone, zone_key.upper()).value]
        if n < cfg["min"] or n > cfg["max"]:
            errors.append({
                "code": f"{zone_key.upper()}_COUNT",
                "message": f"{label} deve ter entre {cfg['min']} e {cfg['max']} cartas "
                           f"(atual: {n}).",
                "zone": getattr(Zone, zone_key.upper()).value,
                "current_quantity": n,
                "allowed_quantity": cfg["max"],
            })

    check_zone("main_deck", "Main Deck")
    check_zone("ride_deck", "Ride Deck")

    limit = rules["copies_per_identity"]
    for uuid, qty in per_identity.items():
        if qty > limit:
            errors.append({
                "code": "COPY_LIMIT", "card_id": uuid,
                "message": f"Máximo de {limit} cópias por carta (atual: {qty}).",
                "current_quantity": qty, "allowed_quantity": limit,
            })

    if rules.get("trigger_count") and counts[Zone.MAIN_DECK.value] >= 50:
        want = rules["trigger_count"]
        if trigger_count != want:
            warnings.append({
                "code": "TRIGGER_COUNT",
                "message": f"Standard exige {want} triggers (atual: {trigger_count}).",
            })

    return {
        "is_valid": len(errors) == 0,
        "basic": True,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "main_deck_count": counts[Zone.MAIN_DECK.value],
            "ride_deck_count": counts[Zone.RIDE_DECK.value],
            "g_deck_count": counts[Zone.G_DECK.value],
            "trigger_count": trigger_count,
            "distinct_cards": len(per_identity),
        },
    }
