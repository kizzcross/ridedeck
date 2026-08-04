"""Enrich imported cards with Nation and Clan from the Fandom wiki.

Strategy: crawl nation categories (authoritative for nation) and clan categories
(authoritative for clan), matching wiki titles to local cards by base name.
Idempotent — safe to re-run; only fills/updates the two fields.
"""
from __future__ import annotations

import logging
from collections import defaultdict

from apps.cards.models import Card

from .adapters.fandom import (
    CLAN_TO_NATION,
    NATION_CATEGORIES,
    FandomClient,
    base_name,
)

logger = logging.getLogger("imports")


def _index_cards_by_base() -> dict[str, list[int]]:
    index: dict[str, list[int]] = defaultdict(list)
    for card in Card.objects.all().only("id", "name"):
        index[base_name(card.name)].append(card.id)
    return index


def enrich_from_fandom(*, rate_limit_per_sec: float = 5.0, log=logger.info) -> dict:
    client = FandomClient(rate_limit_per_sec)
    index = _index_cards_by_base()

    nation_by_id: dict[int, str] = {}
    clan_by_id: dict[int, str] = {}

    # Pass A — nations (authoritative)
    for category, slug in NATION_CATEGORIES.items():
        titles = client.category_members(category)
        hits = 0
        for title in titles:
            for cid in index.get(base_name(title), ()):
                nation_by_id[cid] = slug
                hits += 1
        log(f"nation '{category}': {len(titles)} wiki cards → {hits} matched")

    # Pass B — clans (authoritative for clan). A card that has a clan is a
    # classic/G-era card, so its clan's nation takes precedence over any D-era
    # nation category that base-name-matched the same title (e.g. reprints like
    # "Blaster Blade" that exist in multiple eras).
    for clan, nation_slug in CLAN_TO_NATION.items():
        titles = client.category_members(clan)
        hits = 0
        for title in titles:
            for cid in index.get(base_name(title), ()):
                clan_by_id[cid] = clan
                nation_by_id[cid] = nation_slug
                hits += 1
        log(f"clan '{clan}': {len(titles)} wiki cards → {hits} matched")

    # Bulk apply
    updated = 0
    to_update: list[Card] = []
    touched_ids = set(nation_by_id) | set(clan_by_id)
    for card in Card.objects.filter(id__in=touched_ids).only("id", "nation", "clan"):
        changed = False
        new_nation = nation_by_id.get(card.id)
        new_clan = clan_by_id.get(card.id)
        if new_nation and card.nation != new_nation:
            card.nation = new_nation
            changed = True
        if new_clan and card.clan != new_clan:
            card.clan = new_clan
            changed = True
        if changed:
            to_update.append(card)
    if to_update:
        Card.objects.bulk_update(to_update, ["nation", "clan"], batch_size=500)
        updated = len(to_update)

    stats = {
        "cards_with_nation": len(nation_by_id),
        "cards_with_clan": len(clan_by_id),
        "updated": updated,
    }
    log(f"enrichment done: {stats}")
    return stats
