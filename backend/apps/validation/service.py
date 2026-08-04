"""Bridge between deck models and the rule engine."""
from __future__ import annotations

from apps.formats.models import GameFormat
from apps.powerlevel.services import power_map

from .engine import DeckLine, ValidationContext, run_engine


def build_lines(version) -> list[DeckLine]:
    return [
        DeckLine(
            card_uuid=str(e.card.uuid),
            name=e.card.name,
            zone=e.zone,
            quantity=e.quantity,
            grade=e.card.grade,
            trigger=e.card.trigger,
            nation=e.card.nation,
            card_type=e.card.card_type,
        )
        for e in version.entries.select_related("card")
    ]


def validate_deck_version(version, *, owned_map=None, power_policy=None, banlist_version=None,
                          reference_date=None) -> dict:
    deck = version.deck
    fmt = GameFormat.objects.filter(code=deck.format_code).first()
    rule_version = fmt.current_version(reference_date) if fmt else None

    ctx = ValidationContext(
        lines=build_lines(version),
        format_code=deck.format_code,
        rule_version=rule_version,
        power_map=power_map(deck.format_code),
        power_policy=power_policy,
        banlist_version=banlist_version,
        owned_map=owned_map or {},
        reference_date=reference_date,
    )
    result = run_engine(ctx)
    result["format_rules_version"] = rule_version.version if rule_version else None
    result["banlist_version"] = banlist_version.version if banlist_version else None
    return result
