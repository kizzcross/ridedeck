"""Parse a pasted banlist into resolved entries (card + restriction), reusing
the fuzzy card resolver from `apps.cards.importer`.

Unlike a deck list, a leading number here is the **allowed limit**, not a
quantity: `0 X` → banned, `1 X` → limit 1, `2 X` → limit 2, `3 X` → limit 3.
Section headers ("Banned", "Limited to 1", …) and inline words ("X — banned")
are also understood. When nothing signals a restriction, the line falls back to
the current section (default: banned).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from apps.cards.importer import _extract_card_number, resolve_one
from apps.cards.models import Card, normalize_name

from .choices import RestrictionType

_COMMENT = re.compile(r"^\s*(#|//|;)")
_LEAD_LIMIT = re.compile(r"^\s*(\d{1,2})\s*[x×.:,)-]?\s+(.+)$")

_BAN_WORDS = {"ban", "banned", "forbidden", "proibida", "proibido", "prohibited", "banida", "banido"}
_LIM1_WORDS = {"limited", "limit", "restricted", "restrita", "restrito", "limitada", "limitado"}
_LIM2_WORDS = {"semi", "semilimited", "semi limited", "semi-limited"}

# Section headers → default restriction for following bare-name lines.
_HEADERS = {
    RestrictionType.BANNED: {"banned", "ban", "ban list", "banlist", "forbidden", "proibidas", "banidas"},
    RestrictionType.LIMIT_TO_1: {"limited", "limited to 1", "limit 1", "restricted", "limitadas a 1"},
    RestrictionType.LIMIT_TO_2: {"limited to 2", "limit 2", "semi-limited", "semi limited", "limitadas a 2"},
}
_HEADER_LOOKUP = {kw: rt for rt, kws in _HEADERS.items() for kw in kws}


@dataclass
class ResolvedBanEntry:
    raw: str
    input_name: str
    restriction_type: str
    limit_value: int | None
    card: Card | None = None
    confidence: str = "unmatched"
    score: float = 0.0
    suggestions: list = field(default_factory=list)


def _limit_to_restriction(limit: int) -> tuple[str, int | None]:
    if limit <= 0:
        return RestrictionType.BANNED, None
    if limit == 1:
        return RestrictionType.LIMIT_TO_1, None
    if limit == 2:
        return RestrictionType.LIMIT_TO_2, None
    return RestrictionType.LIMIT_TO_N, limit


def _inline_restriction(text: str) -> tuple[str, int | None, str] | None:
    """Detect a restriction word inside the line; return (rt, limit, cleaned_name)."""
    low = text.lower()
    # e.g. "Card (limited 1)" / "Card - banned" / "Card: semi"
    for sep in ("(", "[", " - ", " — ", ":", "|"):
        if sep in text:
            head, _, tail = text.partition(sep)
            tail_norm = normalize_name(tail)
            words = set(tail_norm.split())
            num = re.search(r"\d", tail_norm)
            if words & _BAN_WORDS:
                return RestrictionType.BANNED, None, head.strip()
            if words & _LIM2_WORDS or "semi" in tail_norm:
                return RestrictionType.LIMIT_TO_2, None, head.strip()
            if words & _LIM1_WORDS:
                lim = int(num.group()) if num else 1
                return _limit_to_restriction(lim) + (head.strip(),)
    if any(w in low for w in ("banned", "forbidden", "banida")):
        return RestrictionType.BANNED, None, re.sub(r"(?i)\b(banned|forbidden|banida|banido)\b", "", text).strip(" -—:|")
    return None


def parse_banlist(text: str) -> list[ResolvedBanEntry]:
    current: str = RestrictionType.BANNED
    out: list[ResolvedBanEntry] = []
    for raw in text.replace("\t", "  ").splitlines():
        line = raw.strip()
        if not line or _COMMENT.match(line):
            continue
        header = _HEADER_LOOKUP.get(normalize_name(line.rstrip(":.-").strip()))
        if header:
            current = header
            continue

        rt: str | None = None
        limit: int | None = None
        rest = line

        lead = _LEAD_LIMIT.match(line)
        inline = _inline_restriction(line)
        if inline:
            rt, limit, rest = inline
        elif lead:
            rt, limit = _limit_to_restriction(int(lead.group(1)))
            rest = lead.group(2)
        else:
            rt, limit = current, None

        name, number = _extract_card_number(rest)
        if not name and not number:
            continue
        r = resolve_one(name, number)
        out.append(ResolvedBanEntry(
            raw=line, input_name=name, restriction_type=rt, limit_value=limit,
            card=r.card, confidence=r.confidence, score=r.score, suggestions=r.suggestions,
        ))
    return out
