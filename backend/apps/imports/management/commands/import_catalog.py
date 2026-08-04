"""Import the real card catalog from a configured data source.

Examples:
    # Cardfight!! Vanguard, G + D series only (skips V), from TCGCSV:
    python manage.py import_catalog --source tcgcsv --series G,D

    # A single set (by group id):
    python manage.py import_catalog --source tcgcsv --set 24636
"""
from django.core.management.base import BaseCommand

from apps.cards.models import Card, CardPrinting, CardSet
from apps.imports.services import ImportRunner, ensure_source


class Command(BaseCommand):
    help = "Import sets + cards from a data source (default: tcgcsv, series G+D)."

    def add_arguments(self, parser):
        parser.add_argument("--source", default="tcgcsv")
        parser.add_argument("--series", default="G,D",
                            help="Comma-separated series to include (D,G,V). Empty = all.")
        parser.add_argument("--category", default="16")
        parser.add_argument("--set", default=None, help="Import only this group/set id.")
        parser.add_argument("--rate", type=int, default=8)
        parser.add_argument("--drop-fixture", action="store_true",
                            help="Delete offline fixture data before importing.")

    def handle(self, *args, **opts):
        series = [s.strip().upper() for s in opts["series"].split(",") if s.strip()]
        source = ensure_source(
            opts["source"], f"{opts['source']} import",
            base_url="https://tcgcsv.com",
            config={"category_id": opts["category"], "series": series,
                    "rate_limit_per_sec": opts["rate"]},
        )
        # keep config current even if the source already existed
        source.config.update({"category_id": opts["category"], "series": series,
                              "rate_limit_per_sec": opts["rate"]})
        source.base_url = "https://tcgcsv.com"
        source.save()

        if opts["drop_fixture"]:
            self._drop_fixture()

        runner = ImportRunner(source, triggered_by="import_catalog")
        self.stdout.write("Importing sets…")
        sets_batch = runner.import_sets()
        self.stdout.write(f"  sets: {sets_batch.status} {sets_batch.metrics}")

        targets = ([CardSet.objects.get(external_source=source.key, external_id=opts["set"])]
                   if opts["set"] else
                   list(CardSet.objects.filter(external_source=source.key).order_by("code")))
        total = len(targets)
        self.stdout.write(f"Importing cards from {total} sets…")
        for i, s in enumerate(targets, 1):
            batch = runner.import_cards(s.external_id)
            self.stdout.write(
                f"  [{i}/{total}] {s.code}: +{batch.created} ~{batch.updated} "
                f"(cards total: {Card.objects.count()})"
            )
        self.stdout.write(self.style.SUCCESS(
            f"Done. Cards: {Card.objects.count()} · Printings: {CardPrinting.objects.count()} "
            f"· Sets: {CardSet.objects.filter(external_source=source.key).count()}"
        ))

    def _drop_fixture(self):
        fixture_sets = CardSet.objects.filter(external_source="fixture")
        CardPrinting.objects.filter(data_source="fixture").delete()
        CardPrinting.objects.filter(card_set__in=fixture_sets).delete()
        orphan = Card.objects.filter(printings__isnull=True)
        count = orphan.count()
        orphan.delete()
        fixture_sets.delete()
        self.stdout.write(f"  dropped fixture data ({count} orphan cards removed)")
