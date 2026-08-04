"""Offline fixture adapter — generates deterministic, fictional cards.

Lets the whole import pipeline run without any network, and provides the dev
catalog (3 sets, 30 cards across nations/grades/triggers). No protected material.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from .base import BaseAdapter, CardRecord, SetRecord

_SETS = [
    ("SET-ALPHA", "Dawn of the Vanguard", date(2024, 1, 12)),
    ("SET-BETA", "Storm of Nations", date(2024, 6, 21)),
    ("SET-GAMMA", "Eternal Ride", date(2025, 2, 14)),
]

_NATIONS = [
    "dragon_empire", "dark_states", "brandt_gate",
    "keter_sanctuary", "stoicheia", "lyrical_monasterio",
]

_ADJ = ["Blazing", "Frozen", "Radiant", "Shadow", "Thunder", "Verdant", "Astral", "Iron"]
_NOUN = ["Dragon", "Knight", "Maiden", "Golem", "Serpent", "Phoenix", "Warden", "Oracle"]


def _trigger_for(index: int) -> tuple[str, int, int]:
    """Return (trigger, shield, critical) cycling through trigger kinds for G0s."""
    kinds = [
        ("critical", 10000, 2),
        ("draw", 10000, 1),
        ("front", 10000, 1),
        ("heal", 10000, 1),
        ("stand", 10000, 1),
        ("", 10000, 1),
    ]
    return kinds[index % len(kinds)]


class FixtureAdapter(BaseAdapter):
    key = "fixture"

    def fetch_sets(self) -> list[SetRecord]:
        return [
            SetRecord(external_id=code, code=code, name=name, release_date=rd,
                      raw={"code": code, "name": name})
            for code, name, rd in _SETS
        ]

    def fetch_cards(self, set_external_id: str | None = None) -> list[CardRecord]:
        cards: list[CardRecord] = []
        idx = 0
        for set_code, _, _rd in _SETS:
            if set_external_id and set_code != set_external_id:
                continue
            for n in range(10):  # 10 cards per set → 30 total
                idx += 1
                nation = _NATIONS[idx % len(_NATIONS)]
                grade = n % 5  # 0..4
                name = f"{_ADJ[idx % len(_ADJ)]} {_NOUN[(idx // 2) % len(_NOUN)]} #{idx}"
                number = f"{set_code}-{n + 1:03d}"

                if grade == 0:
                    trigger, shield, critical = _trigger_for(idx)
                    ctype = "trigger_unit" if trigger else "normal_unit"
                    power = 10000
                elif grade == 4:
                    trigger, shield, critical = "", 0, 1
                    ctype = "g_unit"
                    power = 15000 + (idx % 3) * 1000
                else:
                    trigger, shield, critical = "", 5000 if grade == 1 else 0, 1
                    ctype = "normal_unit"
                    power = 8000 + grade * 3000

                cards.append(
                    CardRecord(
                        external_id=f"fixture-{number}",
                        name=name,
                        card_number=number,
                        set_external_id=set_code,
                        grade=grade,
                        power=power,
                        shield=shield,
                        critical=critical,
                        card_type=ctype,
                        trigger=trigger,
                        nation=nation,
                        race=["Dragon", "Human", "Elf", "Golem"][idx % 4],
                        ability_text=(
                            f"[AUTO]: When this unit rides, draw a card. "
                            f"({name} is fictional dev data.)"
                        ),
                        keywords=["Ride"] if grade in (1, 2, 3) else [],
                        rarity=["C", "R", "RR", "RRR"][idx % 4],
                        illustrator=f"Artist {chr(65 + idx % 6)}",
                        finish="foil" if idx % 5 == 0 else "",
                        image_url="",
                        price=Decimal(f"{1 + (idx % 20)}.{(idx * 7) % 100:02d}"),
                        formats=["standard"] + (["v_premium", "premium"] if grade < 4 else ["premium"]),
                        external_identifiers={"fixture": f"fixture-{number}"},
                        raw={"number": number, "set": set_code},
                    )
                )
        return cards
