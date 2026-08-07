"""Fandom (cardfight.fandom.com) enrichment adapter.

TCGplayer data lacks Nation and Clan. This isolated adapter fills them from the
community wiki's MediaWiki API using **category membership** — one paginated
crawl per nation/clan instead of a page fetch per card.

Kept separate from the card domain and from the price adapter. Respects a polite
rate limit and identifies itself via User-Agent. No scraping of rendered HTML —
only the public JSON API.
"""
from __future__ import annotations

import re
import time
import urllib.parse
import urllib.request

_API = "https://cardfight.fandom.com/api.php"
_USER_AGENT = "RideDeck/1.0 (card catalog enrichment; dev)"

# Nation categories → stored nation slug. Authoritative for nation (both eras).
NATION_CATEGORIES: dict[str, str] = {
    # D-era
    "Dragon Empire": "dragon_empire",
    "Dark States": "dark_states",
    "Brandt Gate": "brandt_gate",
    "Keter Sanctuary": "keter_sanctuary",
    "Stoicheia": "stoicheia",
    "Lyrical Monasterio": "lyrical_monasterio",
    # Original / G-era
    "United Sanctuary": "united_sanctuary",
    "Dark Zone": "dark_zone",
    "Magallanica": "magallanica",
    "Zoo": "zoo",
    "Star Gate": "star_gate",
}

# Trigger categories → trigger slug. TCGplayer doesn't expose trigger type, so we
# take it from the wiki (Heal/Over don't contain their word in the card text).
TRIGGER_CATEGORIES: dict[str, str] = {
    "Critical Trigger": "critical",
    "Draw Trigger": "draw",
    "Heal Trigger": "heal",
    "Front Trigger": "front",
    "Stand Trigger": "stand",
    "Over Trigger": "over",
}

# Clan categories → clan name + the nation it belongs to (for cards the nation
# category crawl might miss). Nation crawl still takes precedence.
CLAN_TO_NATION: dict[str, str] = {
    "Royal Paladin": "united_sanctuary",
    "Shadow Paladin": "united_sanctuary",
    "Gold Paladin": "united_sanctuary",
    "Oracle Think Tank": "united_sanctuary",
    "Angel Feather": "united_sanctuary",
    "Genesis": "united_sanctuary",
    "Kagero": "dragon_empire",
    "Narukami": "dragon_empire",
    "Nubatama": "dragon_empire",
    "Murakumo": "dragon_empire",
    "Tachikaze": "dragon_empire",
    "Nova Grappler": "star_gate",
    "Dimension Police": "star_gate",
    "Link Joker": "star_gate",
    "Spike Brothers": "dark_zone",
    "Dark Irregulars": "dark_zone",
    "Pale Moon": "dark_zone",
    "Gear Chronicle": "dark_zone",
    "Granblue": "magallanica",
    "Bermuda Triangle": "magallanica",
    "Aqua Force": "magallanica",
    "Megacolony": "zoo",
    "Great Nature": "zoo",
    "Neo Nectar": "zoo",
}


def base_name(name: str) -> str:
    """Normalize for matching: drop parentheticals ((V Series)/(ZERO)/(Re+)…),
    strip punctuation, collapse whitespace, lowercase."""
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"[^\w\s]", " ", name.lower())
    return re.sub(r"\s+", " ", name).strip()


class FandomClient:
    def __init__(self, rate_limit_per_sec: float = 5.0):
        self.min_interval = 1.0 / max(rate_limit_per_sec, 0.5)
        self._last = 0.0

    def _get(self, params: dict) -> dict:
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        url = _API + "?" + urllib.parse.urlencode({**params, "format": "json"})
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    import json

                    return json.load(resp)
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(min(2**attempt, 8))
        return {}

    def category_members(self, category: str) -> list[str]:
        """All main-namespace page titles in a category (paginated)."""
        out: list[str] = []
        cont = None
        while True:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": "500",
                "cmnamespace": "0",
            }
            if cont:
                params["cmcontinue"] = cont
            data = self._get(params)
            out += [m["title"] for m in data.get("query", {}).get("categorymembers", [])]
            cont = data.get("continue", {}).get("cmcontinue")
            if not cont:
                break
        return out
