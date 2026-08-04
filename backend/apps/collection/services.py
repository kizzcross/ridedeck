"""Collection aggregation + deck ownership report."""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.cards.models import CardPrinting

from .models import CollectionPrinting, UserCollectionItem


def owned_map(user) -> dict[str, int]:
    """{card_uuid: total_owned_quantity} aggregated by canonical identity."""
    rows = (
        CollectionPrinting.objects.filter(item__user=user)
        .values("item__card__uuid")
        .annotate(total=Sum("quantity"))
    )
    return {str(r["item__card__uuid"]): r["total"] for r in rows}


@transaction.atomic
def upsert_owned(user, printing: CardPrinting, *, quantity: int, condition: str,
                 language: str, finish: str, price_paid=None) -> CollectionPrinting | None:
    """Set the owned quantity for a printing/condition/language/finish combo.
    quantity<=0 removes it. Returns the row or None."""
    item, _ = UserCollectionItem.objects.get_or_create(user=user, card=printing.card)
    if quantity <= 0:
        CollectionPrinting.objects.filter(
            item=item, printing=printing, language=language, condition=condition, finish=finish
        ).delete()
        if not item.printings.exists():
            item.delete()
        return None
    obj, _ = CollectionPrinting.objects.update_or_create(
        item=item, printing=printing, language=language, condition=condition, finish=finish,
        defaults={"quantity": quantity, "price_paid": price_paid},
    )
    return obj


def _cheapest_price(card) -> Decimal | None:
    prices = [p.price for p in card.printings.all() if p.price is not None]
    return min(prices) if prices else None


def deck_collection_report(version, user) -> dict:
    """Per-entry owned/missing + totals + shopping list with a price estimate.

    Missing copies are informational only — never an error.
    """
    owned = owned_map(user)
    entries = list(version.entries.select_related("card").prefetch_related("card__printings"))

    lines = []
    total_used = total_owned = total_missing = 0
    missing_cost = Decimal("0")

    for e in entries:
        used = e.quantity
        have = min(owned.get(str(e.card.uuid), 0), used)
        missing = max(0, used - owned.get(str(e.card.uuid), 0))
        total_used += used
        total_owned += have
        total_missing += missing
        unit = _cheapest_price(e.card)
        line_cost = (unit * missing) if (unit and missing) else None
        if line_cost:
            missing_cost += line_cost
        if missing > 0:
            lines.append({
                "card_uuid": str(e.card.uuid),
                "card_name": e.card.name,
                "zone": e.zone,
                "used": used,
                "owned": owned.get(str(e.card.uuid), 0),
                "missing": missing,
                "unit_price": str(unit) if unit else None,
                "line_cost": str(line_cost) if line_cost else None,
            })

    pct = round((total_owned / total_used) * 100) if total_used else 100
    return {
        "summary": {
            "used": total_used,
            "owned": total_owned,
            "missing": total_missing,
            "owned_pct": pct,
            "missing_cost_estimate": str(missing_cost) if missing_cost else None,
        },
        "shopping_list": sorted(lines, key=lambda x: -x["missing"]),
    }
