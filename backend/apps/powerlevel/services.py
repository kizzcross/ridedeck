"""Power level mutations (audited) + deck power calculation."""
from __future__ import annotations

from django.db import transaction

from apps.common.models import record_audit

from .models import (
    CardPowerLevel,
    CardPowerLevelHistory,
    PowerLevelScale,
)


def default_scale() -> PowerLevelScale:
    scale = PowerLevelScale.objects.filter(is_active=True).first()
    if not scale:
        scale = PowerLevelScale.objects.create(
            name="Default 1-10", min_value=1, max_value=10,
            descriptions={str(i): d for i, d in enumerate([
                "", "impacto muito baixo", "impacto baixo", "abaixo da média",
                "situacional", "nível médio", "forte", "muito forte", "dominante",
                "extremamente dominante", "format-warping",
            ]) if i},
        )
    return scale


@transaction.atomic
def set_power_level(*, admin, card, format_code: str, value: int, justification: str,
                    status: str = CardPowerLevel.Status.PUBLISHED,
                    source: str = CardPowerLevelHistory.Source.ADMIN_SINGLE,
                    confidence=None, tags=None) -> CardPowerLevel:
    """Create/update a card's power level for a format. Admin-only (enforced by
    the view). Always writes a history row + audit entry."""
    scale = default_scale()
    if not (scale.min_value <= value <= scale.max_value):
        raise ValueError(f"value must be within {scale.min_value}-{scale.max_value}")

    existing = CardPowerLevel.objects.filter(card=card, format_code=format_code).first()
    previous = existing.value if existing else None
    new_version = (existing.version + 1) if existing else 1

    obj, _ = CardPowerLevel.objects.update_or_create(
        card=card, format_code=format_code,
        defaults={
            "scale": scale, "value": value, "status": status,
            "justification": justification, "confidence": confidence,
            "tags": tags or [], "version": new_version, "updated_by": admin,
        },
    )

    CardPowerLevelHistory.objects.create(
        card=card, format_code=format_code, previous_value=previous, new_value=value,
        admin=admin, justification=justification, source=source, version=new_version,
    )
    record_audit(
        action="power_level_change", actor=admin, target=card,
        summary=f"Power level {previous}→{value} @ {format_code}",
        payload={"card": str(card.uuid), "format": format_code, "previous": previous,
                 "new": value, "version": new_version, "justification": justification,
                 "source": source},
        source=source,
    )
    return obj


@transaction.atomic
def bulk_set_power_level(*, admin, cards, format_code: str, value: int, justification: str):
    """Apply the same level to many cards at once (audited individually)."""
    results = []
    for card in cards:
        results.append(set_power_level(
            admin=admin, card=card, format_code=format_code, value=value,
            justification=justification, source=CardPowerLevelHistory.Source.ADMIN_BULK,
        ))
    return results


def power_map(format_code: str) -> dict[str, int]:
    """{card_uuid: published_value} for a format."""
    rows = CardPowerLevel.objects.filter(
        format_code=format_code, status=CardPowerLevel.Status.PUBLISHED
    ).values_list("card__uuid", "value")
    return {str(u): v for u, v in rows}


def deck_power_stats(version, format_code: str) -> dict:
    """Compute deck power metrics. NOT a simple average — returns max, simple &
    weighted averages, weighted sum, distribution and top contributors."""
    pmap = power_map(format_code)
    entries = list(version.entries.select_related("card"))

    rated = []          # (card, value, qty)
    unrated = 0
    for e in entries:
        v = pmap.get(str(e.card.uuid))
        if v is None:
            unrated += e.quantity
        else:
            rated.append((e.card, v, e.quantity))

    if not rated:
        return {"has_data": False, "unrated_cards": unrated}

    total_qty = sum(q for _, _, q in rated)
    values = [v for _, v, _ in rated]
    weighted_sum = sum(v * q for _, v, q in rated)
    distribution: dict[int, int] = {}
    for _, v, q in rated:
        distribution[v] = distribution.get(v, 0) + q

    def count_above(threshold):
        return sum(q for _, v, q in rated if v >= threshold)

    top = sorted(rated, key=lambda x: (-x[1], x[0].name))[:5]

    return {
        "has_data": True,
        "format_code": format_code,
        "max_power_level": max(values),
        "simple_average": round(sum(values) / len(values), 2),
        "weighted_average": round(weighted_sum / total_qty, 2),
        "weighted_sum": weighted_sum,
        "distribution": {str(k): distribution[k] for k in sorted(distribution)},
        "count_at_or_above": {str(t): count_above(t) for t in (6, 7, 8, 9, 10)},
        "unrated_cards": unrated,
        "top_contributors": [
            {"card_uuid": str(c.uuid), "name": c.name, "value": v, "quantity": q}
            for c, v, q in top
        ],
        "editorial_note": "O único dado editorial oficial é o power level individual "
                          "das cartas, definido pelos administradores.",
    }
