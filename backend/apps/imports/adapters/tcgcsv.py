"""TCGCSV / TCGplayer adapter for Cardfight!! Vanguard (category 16).

Fetches groups (sets) and products (cards) from https://tcgcsv.com. Network
access is wrapped with retry+backoff and a simple rate limit. Game fields come
from TCGplayer "extendedData" (Number, Grade, Power, Shield, Critical, Unit…).

Sealed products (no "Number") are skipped — only real singles are imported.
A `series` config (e.g. ["G", "D"]) restricts which sets are pulled.
"""
from __future__ import annotations

import re
import time
from decimal import Decimal, InvalidOperation

import requests

from .base import BaseAdapter, CardRecord, PriceRecord, SetRecord

_DEFAULT_BASE = "https://tcgcsv.com"
_USER_AGENT = "RideDeck/1.0 (+https://ridedeck.local) card-catalog-import"

_UNIT_TO_TYPE = {
    "normal unit": "normal_unit",
    "trigger unit": "trigger_unit",
    "g unit": "g_unit",
    "normal order": "order",
    "order": "order",
    "set order": "set_order",
    "blitz order": "blitz_order",
    "token": "token",
}

_TRIGGER_WORDS = {
    "critical": "critical", "draw": "draw", "front": "front",
    "heal": "heal", "stand": "stand", "over": "over",
}


def _to_decimal(value) -> Decimal | None:
    try:
        d = Decimal(str(value))
        return d if d > 0 else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def _int(value, default=None):
    digits = "".join(c for c in str(value) if c.isdigit() or c == "-")
    try:
        return int(digits)
    except (TypeError, ValueError):
        return default


def _ext(product: dict) -> dict[str, str]:
    return {
        item.get("name", ""): item.get("value", "")
        for item in product.get("extendedData", [])
        if isinstance(item, dict)
    }


def set_code_from_name(name: str, fallback: str = "") -> str:
    """The real set code lives in the group name (e.g. "D-SS11: ..."). The
    `abbreviation` field is unreliable, so parse the name's leading token."""
    m = re.match(r"^\s*([A-Za-z]{1,3}Z?-[A-Za-z0-9]+)", name or "")
    if m:
        return m.group(1).upper()
    return (fallback or (name or "")[:16]).upper()


def series_of(code: str) -> str:
    c = (code or "").upper()
    if c.startswith("DZ") or c.startswith("D-"):
        return "D"
    if c.startswith("G-"):
        return "G"
    if c.startswith("V-"):
        return "V"
    return "OTHER"


class TCGCSVAdapter(BaseAdapter):
    key = "tcgcsv"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        base = self.config.get("base_url") or _DEFAULT_BASE
        self.base_url = base.rstrip("/")
        self.category_id = str(self.config.get("category_id", "16"))
        self.series = [s.upper() for s in self.config.get("series", ["G", "D"])]
        self.rate_limit_per_sec = int(self.config.get("rate_limit_per_sec", 5))
        self.max_retries = int(self.config.get("max_retries", 4))
        self._last_call = 0.0
        self._group_code: dict[str, str] = {}
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": _USER_AGENT, "Accept": "application/json"})

    # -- HTTP with rate limit + exponential backoff -------------------------
    def _get(self, path: str) -> dict:
        min_interval = 1.0 / max(self.rate_limit_per_sec, 1)
        for attempt in range(self.max_retries):
            wait = min_interval - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            try:
                resp = self.session.get(f"{self.base_url}{path}", timeout=30)
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise requests.HTTPError(f"status {resp.status_code}")
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, ValueError):
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(min(2**attempt, 8))
        return {}

    # -- Adapter API --------------------------------------------------------
    def fetch_sets(self) -> list[SetRecord]:
        data = self._get(f"/tcgplayer/{self.category_id}/groups")
        groups = data.get("results", data if isinstance(data, list) else [])
        out: list[SetRecord] = []
        for g in groups:
            code = set_code_from_name(g.get("name", ""), g.get("abbreviation", ""))
            self._group_code[str(g.get("groupId"))] = code
            if self.series and series_of(code) not in self.series:
                continue
            out.append(
                SetRecord(
                    external_id=str(g.get("groupId")),
                    code=code,
                    name=g.get("name", ""),
                    raw=g,
                )
            )
        return out

    def _code_for_group(self, group_id: str) -> str:
        if group_id not in self._group_code:
            self.fetch_sets()  # populates the group→code map (respects series)
        return self._group_code.get(str(group_id), "")

    def fetch_cards(self, set_external_id: str | None = None) -> list[CardRecord]:
        if not set_external_id:
            raise ValueError("TCGCSV requires a set/group id to fetch cards.")
        set_code = self._code_for_group(str(set_external_id))
        data = self._get(f"/tcgplayer/{self.category_id}/{set_external_id}/products")
        products = data.get("results", data if isinstance(data, list) else [])
        out: list[CardRecord] = []
        for p in products:
            ext = _ext(p)
            number = ext.get("Number", "").strip()
            if not number:
                continue  # sealed product / not a single — skip
            unit = ext.get("Unit", "").strip().lower()
            card_type = _UNIT_TO_TYPE.get(unit, "normal_unit")
            name = p.get("name", "")
            trigger = ""
            if card_type == "trigger_unit":
                for word, t in _TRIGGER_WORDS.items():
                    if word in name.lower() or word in ext.get("Description", "").lower()[:40]:
                        trigger = t
                        break
            out.append(
                CardRecord(
                    external_id=str(p.get("productId")),
                    name=name,
                    card_number=number,
                    set_external_id=str(set_external_id),
                    grade=_int(ext.get("Grade", "0"), 0) or 0,
                    power=_int(ext.get("Power", "")) or None,
                    shield=_int(ext.get("Shield", "")),
                    critical=_int(ext.get("Critical", "1"), 1) or 1,
                    card_type=card_type,
                    trigger=trigger,
                    nation=ext.get("Nation", ""),
                    clan=ext.get("Clan", ""),
                    race=ext.get("Race", ""),
                    ability_text=ext.get("Description", ""),
                    rarity=ext.get("Rarity", ""),
                    illustrator=ext.get("Illustrator", ""),
                    image_url=p.get("imageUrl", ""),
                    formats=self._formats_for(set_code),
                    external_identifiers={"tcgplayer": str(p.get("productId"))},
                    raw=p,
                )
            )
        return out

    def _formats_for(self, code: str) -> list[str]:
        s = series_of(code)
        if s == "D":
            return ["standard", "premium"]
        if s == "G":
            return ["g", "premium"]
        return ["premium"]

    def fetch_prices(self) -> list[PriceRecord]:
        data = self._get(f"/tcgplayer/{self.category_id}/prices")
        results = data.get("results", data if isinstance(data, list) else [])
        out: list[PriceRecord] = []
        for r in results:
            price = _to_decimal(r.get("marketPrice") or r.get("midPrice"))
            if price is not None:
                out.append(PriceRecord(supplier_product_id=str(r.get("productId")), price=price, raw=r))
        return out
