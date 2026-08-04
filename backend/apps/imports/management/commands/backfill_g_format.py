"""Backfill 'g' format legality for existing G-era cards (set code starts with G-).

Run once after adding the G format; no network needed. Idempotent.
"""
from django.core.management.base import BaseCommand

from apps.cards.models import Card, CardFormatLegality


class Command(BaseCommand):
    help = "Tag G-era cards (G-series sets) as legal in the 'g' format."

    def handle(self, *args, **opts):
        g_cards = (
            Card.objects.filter(printings__card_set__code__istartswith="g-")
            .distinct()
            .only("id")
        )
        created = 0
        for card in g_cards.iterator():
            _, was_created = CardFormatLegality.objects.get_or_create(
                card_id=card.id, format_code="g", defaults={"legality": "legal"}
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(
            f"G format legality: {g_cards.count()} G-era cards, {created} novas entradas."))
