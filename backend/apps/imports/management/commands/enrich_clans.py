"""Fill Nation + Clan on imported cards from the Fandom wiki.

    python manage.py enrich_clans
"""
from django.core.management.base import BaseCommand

from apps.imports.enrichment import enrich_from_fandom


class Command(BaseCommand):
    help = "Enrich cards with Nation and Clan from the Cardfight Fandom wiki."

    def add_arguments(self, parser):
        parser.add_argument("--rate", type=float, default=6.0,
                            help="Max requests/sec to the wiki API.")

    def handle(self, *args, **opts):
        stats = enrich_from_fandom(
            rate_limit_per_sec=opts["rate"],
            log=lambda m: self.stdout.write(f"  {m}"),
        )
        self.stdout.write(self.style.SUCCESS(f"Done: {stats}"))
