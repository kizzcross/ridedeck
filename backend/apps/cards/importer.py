"""Text deck/banlist list parsing + fuzzy card resolution.

Accepts many hand-written list formats and resolves each line to a canonical
`Card`, tolerating typos via Postgres trigram similarity (pg_trgm is already
enabled with a GIN index on `Card.name`). The parser never guesses silently:
every line comes back with a confidence and, when unsure, alternative
suggestions the user can pick from.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from django.contrib.postgres.search import TrigramSimilarity

from .models import Card, CardPrinting, normalize_name

# ---- Parsing ---------------------------------------------------------------

# A Vanguard card number, e.g. BT01/001, D-BT01/001EN, V-EB01/OR01.
_CARD_NUMBER = re.compile(r"\b([A-Za-z]{1,5}-?[A-Za-z]{0,3}\d{0,3}/[A-Za-z]{0,3}\d{1,3}[A-Za-z]{0,3})\b")
# Quantity markers: "4x", "4×", "x4", "×4", "4" (leading) or "x4"/"(4)" (trailing).
_LEAD_QTY = re.compile(r"^\s*(?:[xX×]\s*)?(\d{1,2})\s*[xX×]?[\s.:,)-]+\s*(.+)$")
_TRAIL_QTY = re.compile(r"^(.+?)\s*(?:[xX×]\s*(\d{1,2})|\((\d{1,2})\))\s*$")

# Section headers → zone. The whole line (minus punctuation) must match.
_ZONE_HEADERS = {
    "main_deck": {"main", "main deck", "maindeck", "deck", "grade 0", "grade 1",
                  "grade 2", "grade 3", "triggers", "trigger", "units", "normal unit"},
    "ride_deck": {"ride", "ride deck", "rideline", "ride line", "first vanguard"},
    "g_deck": {"g", "g deck", "g zone", "gzone", "g-zone", "stride", "stride deck"},
}
_ZONE_LOOKUP = {kw: zone for zone, kws in _ZONE_HEADERS.items() for kw in kws}
# Header words that are NOT cards but also should NOT switch zone (just skipped).
_SKIP_HEADERS = {"grade 0", "grade 1", "grade 2", "grade 3", "triggers", "trigger",
                 "units", "normal unit", "deck", "order", "total", "sideboard"}
_COMMENT = re.compile(r"^\s*(#|//|;)")


@dataclass
class ParsedLine:
    raw: str
    quantity: int
    name: str
    card_number: str | None
    zone: str


def _extract_card_number(text: str) -> tuple[str, str | None]:
    """Pull a card number out of the text (parens/brackets/bare) and return the
    cleaned name + the number (or None)."""
    m = _CARD_NUMBER.search(text)
    if not m:
        return text.strip(" ()[]{}-·—"), None
    number = m.group(1)
    cleaned = (text[: m.start()] + " " + text[m.end():]).strip(" ()[]{}-·—")
    return cleaned, number


def _header_zone(line: str) -> str | None:
    key = normalize_name(line.rstrip(":.-").strip())
    return _ZONE_LOOKUP.get(key)


def _is_skippable_header(line: str) -> bool:
    return normalize_name(line.rstrip(":.-").strip()) in _SKIP_HEADERS


def parse_card_list(text: str, default_zone: str = "main_deck") -> list[ParsedLine]:
    """Parse a pasted list into structured lines. Tolerant of many formats:
    `4x Name`, `4 Name`, `Name x4`, `Name (4)`, `Name`, CSV/TSV, and card numbers
    in parens/brackets/bare. Section headers switch the current zone."""
    lines: list[ParsedLine] = []
    zone = default_zone if default_zone in _ZONE_HEADERS else "main_deck"
    for raw in text.replace("\t", "  ").splitlines():
        line = raw.strip()
        if not line or _COMMENT.match(line):
            continue
        # Zone header?
        z = _header_zone(line)
        if z:
            zone = z
            continue
        if _is_skippable_header(line):
            continue
        # CSV "4, Name" or "Name, 4"
        csv = re.match(r"^\s*(\d{1,2})\s*,\s*(.+)$", line) or None
        if csv:
            qty, rest = int(csv.group(1)), csv.group(2)
        else:
            m = _LEAD_QTY.match(line)
            if m:
                qty, rest = int(m.group(1)), m.group(2)
            else:
                t = _TRAIL_QTY.match(line)
                if t:
                    qty = int(t.group(2) or t.group(3))
                    rest = t.group(1)
                else:
                    qty, rest = 1, line
        name, number = _extract_card_number(rest)
        if not name and not number:
            continue
        lines.append(ParsedLine(raw=raw.strip(), quantity=max(1, min(qty, 99)),
                                name=name, card_number=number, zone=zone))
    return lines


# ---- Resolution ------------------------------------------------------------

FUZZY_MATCH = 0.55      # >= this trigram score → confident fuzzy match
FUZZY_SUGGEST = 0.25    # >= this → offer as a suggestion


@dataclass
class ResolvedLine:
    raw: str
    quantity: int
    zone: str
    input_name: str
    card: Card | None = None
    confidence: str = "unmatched"     # exact | code | fuzzy | ambiguous | unmatched
    score: float = 0.0
    suggestions: list[Card] = field(default_factory=list)


def _by_number(number: str) -> Card | None:
    core = re.sub(r"[A-Za-z]+$", "", number)  # drop trailing lang/rarity letters
    pr = (CardPrinting.objects.filter(card_number__istartswith=core)
          .select_related("card").first())
    return pr.card if pr else None


def resolve_one(name: str, number: str | None = None) -> ResolvedLine:
    rl = ResolvedLine(raw=name, quantity=1, zone="main_deck", input_name=name)

    if number:
        card = _by_number(number)
        if card:
            rl.card, rl.confidence, rl.score = card, "code", 1.0
            return rl

    norm = normalize_name(name)
    if norm:
        exact = Card.objects.filter(normalized_name=norm).first()
        if exact:
            rl.card, rl.confidence, rl.score = exact, "exact", 1.0
            return rl

    # Fuzzy: trigram-ranked candidates on the display name.
    candidates = list(
        Card.objects.annotate(sim=TrigramSimilarity("name", name))
        .filter(sim__gte=FUZZY_SUGGEST)
        .order_by("-sim")[:6]
    )
    if candidates:
        top = candidates[0]
        rl.score = round(float(top.sim), 3)
        rl.suggestions = candidates[:5]
        # A confident match above the bar is "fuzzy" (auto-selected). A weaker one
        # is "ambiguous" (best guess, flagged for review). Either way the
        # suggestions are offered so the user can swap to a specific variant.
        rl.card = top
        rl.confidence = "fuzzy" if rl.score >= FUZZY_MATCH else "ambiguous"
    return rl


def resolve_lines(parsed: list[ParsedLine]) -> list[ResolvedLine]:
    out: list[ResolvedLine] = []
    for p in parsed:
        r = resolve_one(p.name, p.card_number)
        r.raw, r.quantity, r.zone, r.input_name = p.raw, p.quantity, p.zone, p.name
        out.append(r)
    return out


def resolve_text(text: str, default_zone: str = "main_deck") -> list[ResolvedLine]:
    return resolve_lines(parse_card_list(text, default_zone=default_zone))
