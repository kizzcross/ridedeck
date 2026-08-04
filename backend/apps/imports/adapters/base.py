"""Adapter contract.

Domain code depends on these dataclasses + the abstract interface, never on a
concrete provider. Add a new provider by implementing `BaseAdapter` and
registering it — nothing else in the codebase changes.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class SetRecord:
    external_id: str
    code: str
    name: str
    release_date: date | None = None
    raw: dict = field(default_factory=dict)


@dataclass
class CardRecord:
    """Provider-neutral card + printing bundle. The service splits it into a
    canonical Card and a CardPrinting during upsert."""

    external_id: str            # stable id at the provider (product id)
    name: str
    card_number: str
    set_external_id: str
    grade: int = 0
    power: int | None = None
    shield: int | None = None
    critical: int = 1
    card_type: str = "normal_unit"
    trigger: str = ""
    nation: str = ""
    clan: str = ""
    race: str = ""
    ability_text: str = ""
    keywords: list[str] = field(default_factory=list)
    rarity: str = ""
    language: str = "en"
    illustrator: str = ""
    finish: str = ""
    image_url: str = ""
    price: Decimal | None = None
    formats: list[str] = field(default_factory=list)
    external_identifiers: dict[str, str] = field(default_factory=dict)
    raw: dict = field(default_factory=dict)


@dataclass
class PriceRecord:
    supplier_product_id: str
    price: Decimal
    currency: str = "USD"
    raw: dict = field(default_factory=dict)


class BaseAdapter(abc.ABC):
    key: str = "base"

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abc.abstractmethod
    def fetch_sets(self) -> list[SetRecord]:
        ...

    @abc.abstractmethod
    def fetch_cards(self, set_external_id: str | None = None) -> list[CardRecord]:
        ...

    def fetch_prices(self) -> list[PriceRecord]:
        return []
