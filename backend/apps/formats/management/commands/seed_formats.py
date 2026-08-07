"""Seed the game formats + their current rule versions (idempotent).

Values here are placeholders for the current metagame and can be superseded by a
new FormatRuleVersion at any time — no code migration needed.
"""
from datetime import date

from django.core.management.base import BaseCommand

from apps.formats.models import (
    FormatConstructionRule,
    FormatRuleVersion,
    FormatTriggerRule,
    FormatZoneRule,
    GameFormat,
)

FORMATS = [
    {
        "code": "standard", "name": "Standard", "sort_order": 1,
        "zones": {"main_deck": (50, 50), "ride_deck": (5, 5), "g_deck": (0, 0)},
        "triggers": {"total": 16, "over": 1, "counted": ["main_deck"], "per_type": {"heal": 4}},
        "construction": {"copies": 4, "nation_locked": True},
    },
    {
        "code": "v_premium", "name": "V Premium", "sort_order": 2,
        "zones": {"main_deck": (50, 50), "ride_deck": (0, 0), "g_deck": (0, 16)},
        "triggers": {"total": 16, "over": 0, "counted": ["main_deck"], "per_type": {"heal": 4}},
        "construction": {"copies": 4, "nation_locked": False, "clan_locked": True},
    },
    {
        "code": "premium", "name": "Premium", "sort_order": 3,
        "zones": {"main_deck": (50, 50), "ride_deck": (0, 0), "g_deck": (0, 16)},
        "triggers": {"total": 16, "over": 0, "counted": ["main_deck"], "per_type": {"heal": 4}},
        "construction": {"copies": 4, "nation_locked": False},
    },
    {
        # G era: Main 50 + G Zone (até 16), sem Ride Deck, travado por Clan.
        "code": "g", "name": "G Era", "sort_order": 4,
        "zones": {"main_deck": (50, 50), "ride_deck": (0, 0), "g_deck": (0, 16)},
        "triggers": {"total": 16, "over": 0, "counted": ["main_deck"], "per_type": {"heal": 4}},
        "construction": {"copies": 4, "nation_locked": False, "clan_locked": True},
    },
]


class Command(BaseCommand):
    help = "Seed game formats and their rule versions."

    def handle(self, *args, **opts):
        for spec in FORMATS:
            fmt, _ = GameFormat.objects.get_or_create(
                code=spec["code"],
                defaults={"name": spec["name"], "sort_order": spec["sort_order"]},
            )
            if fmt.rule_versions.exists():
                self.stdout.write(f"  = {fmt.code}: rules exist")
                continue
            rv = FormatRuleVersion.objects.create(
                game_format=fmt, version=1, valid_from=date(2024, 1, 1),
                notes="Initial seeded ruleset",
            )
            for zone, (mn, mx) in spec["zones"].items():
                FormatZoneRule.objects.create(rule_version=rv, zone=zone, min_count=mn, max_count=mx)
            t = spec["triggers"]
            FormatTriggerRule.objects.create(
                rule_version=rv, total_triggers=t["total"], over_trigger_limit=t["over"],
                counted_zones=t["counted"], per_type_limits=t["per_type"],
            )
            c = spec["construction"]
            FormatConstructionRule.objects.create(
                rule_version=rv, copies_per_identity=c["copies"],
                nation_locked=c.get("nation_locked", False),
                clan_locked=c.get("clan_locked", False),
            )
            self.stdout.write(self.style.SUCCESS(f"  + {fmt.code}: seeded rules v1"))
        self.stdout.write(self.style.SUCCESS("Formats seeded."))
