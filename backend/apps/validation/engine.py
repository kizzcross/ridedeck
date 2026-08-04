"""Centralized deck validation rule engine (backend = source of truth).

Rules are pluggable. The engine loads the current FormatRuleVersion for the
deck's format at a reference date and runs each rule, collecting structured
errors and warnings. Categories are kept strictly separate — in particular,
missing collection copies are always a WARNING, never an error.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import date

from django.utils import timezone


@dataclass
class DeckLine:
    card_uuid: str
    name: str
    zone: str
    quantity: int
    grade: int
    trigger: str
    nation: str
    card_type: str


@dataclass
class ValidationContext:
    lines: list[DeckLine]
    format_code: str
    rule_version: object | None          # formats.FormatRuleVersion
    power_map: dict[str, int] = field(default_factory=dict)
    power_policy: object | None = None   # powerlevel.TournamentPowerPolicy
    banlist_version: object | None = None  # banlists.BanlistVersion
    owned_map: dict[str, int] = field(default_factory=dict)
    reference_date: date | None = None

    def zone_count(self, zone: str) -> int:
        return sum(line.quantity for line in self.lines if line.zone == zone)

    def trigger_count(self, zones=None) -> int:
        return sum(
            line.quantity for line in self.lines
            if line.trigger and (zones is None or line.zone in zones)
        )


class Rule(abc.ABC):
    code = "rule"

    @abc.abstractmethod
    def check(self, ctx: ValidationContext) -> list[dict]:
        ...

    @staticmethod
    def error(code, message, **extra) -> dict:
        return {"severity": "error", "code": code, "message": message, **extra}

    @staticmethod
    def warning(code, message, **extra) -> dict:
        return {"severity": "warning", "code": code, "message": message, **extra}


class ZoneCountRule(Rule):
    code = "ZONE_COUNT"

    def check(self, ctx):
        if not ctx.rule_version:
            return []
        out = []
        for zr in ctx.rule_version.zone_rules.all():
            n = ctx.zone_count(zr.zone)
            if n < zr.min_count or n > zr.max_count:
                out.append(self.error(
                    f"{zr.zone.upper()}_COUNT",
                    f"{zr.zone.replace('_', ' ').title()} deve ter entre {zr.min_count} e "
                    f"{zr.max_count} cartas (atual: {n}).",
                    zone=zr.zone, current_quantity=n, allowed_quantity=zr.max_count,
                ))
        return out


class CopyLimitRule(Rule):
    code = "COPY_LIMIT"

    def check(self, ctx):
        cr = getattr(ctx.rule_version, "construction_rule", None) if ctx.rule_version else None
        limit = cr.copies_per_identity if cr else 4
        per_identity: dict[str, tuple[str, int]] = {}
        for line in ctx.lines:
            name, qty = per_identity.get(line.card_uuid, (line.name, 0))
            per_identity[line.card_uuid] = (line.name, qty + line.quantity)
        out = []
        for uuid, (name, qty) in per_identity.items():
            if qty > limit:
                out.append(self.error(
                    "COPY_LIMIT", f"Máximo de {limit} cópias de “{name}” (atual: {qty}).",
                    card_id=uuid, current_quantity=qty, allowed_quantity=limit,
                ))
        return out


class TriggerRule(Rule):
    code = "TRIGGER_COUNT"

    def check(self, ctx):
        tr = getattr(ctx.rule_version, "trigger_rule", None) if ctx.rule_version else None
        if not tr:
            return []
        zones = tr.counted_zones or None
        count = ctx.trigger_count(zones)
        out = []
        # Only enforce once the main deck is at its expected size.
        main = ctx.zone_count("main_deck")
        if main >= 50 and count != tr.total_triggers:
            out.append(self.warning(
                "TRIGGER_COUNT",
                f"O formato exige {tr.total_triggers} triggers (atual: {count}).",
                current_quantity=count, allowed_quantity=tr.total_triggers,
            ))
        # Over-trigger limit
        over = sum(ln.quantity for ln in ctx.lines if ln.trigger == "over")
        if over > tr.over_trigger_limit:
            out.append(self.error(
                "OVER_TRIGGER_LIMIT",
                f"Máximo de {tr.over_trigger_limit} Over Trigger (atual: {over}).",
                current_quantity=over, allowed_quantity=tr.over_trigger_limit,
            ))
        # Per-type limits
        for ttype, limit in (tr.per_type_limits or {}).items():
            n = sum(ln.quantity for ln in ctx.lines if ln.trigger == ttype)
            if n > limit:
                out.append(self.error(
                    "TRIGGER_TYPE_LIMIT",
                    f"Máximo de {limit} triggers do tipo {ttype} (atual: {n}).",
                    current_quantity=n, allowed_quantity=limit,
                ))
        return out


class NationLockRule(Rule):
    code = "NATION_LOCK"

    def check(self, ctx):
        cr = getattr(ctx.rule_version, "construction_rule", None) if ctx.rule_version else None
        if not cr or not cr.nation_locked:
            return []
        nations = {ln.nation for ln in ctx.lines if ln.zone == "main_deck" and ln.nation}
        if len(nations) > 1:
            return [self.error(
                "MULTIPLE_NATIONS",
                f"Formato trava por Nation única — encontradas: {', '.join(sorted(nations))}.",
            )]
        return []


class PowerPolicyRule(Rule):
    code = "POWER_POLICY"

    def check(self, ctx):
        policy = ctx.power_policy
        if not policy:
            return []
        cfg = policy.config or {}
        pm = ctx.power_map
        out = []
        rated = [(ln, pm.get(ln.card_uuid)) for ln in ctx.lines]
        rated = [(ln, v) for ln, v in rated if v is not None]

        if policy.kind == "max_per_card":
            cap = cfg.get("max", 10)
            for ln, v in rated:
                if v > cap:
                    out.append(self.error("POWER_MAX_PER_CARD",
                        f"“{ln.name}” é power {v}, acima do máximo {cap}.", card_id=ln.card_uuid))
        elif policy.kind == "range":
            lo, hi = cfg.get("min", 1), cfg.get("max", 10)
            for ln, v in rated:
                if v < lo or v > hi:
                    out.append(self.error("POWER_RANGE",
                        f"“{ln.name}” (power {v}) fora da faixa {lo}-{hi}.", card_id=ln.card_uuid))
        elif policy.kind == "max_above":
            thr, cap = cfg.get("threshold", 7), cfg.get("max_cards", 4)
            n = sum(ln.quantity for ln, v in rated if v >= thr)
            if n > cap:
                out.append(self.error("POWER_MAX_ABOVE",
                    f"Máximo de {cap} cartas nível ≥{thr} (atual: {n})."))
        elif policy.kind == "point_budget":
            budget = cfg.get("budget", 0)
            total = sum(v * ln.quantity for ln, v in rated
                        if cfg.get("zone", "main_deck") in (ln.zone, "any"))
            if total > budget:
                out.append(self.error("POWER_BUDGET",
                    f"Orçamento de {budget} power points excedido (atual: {total})."))
        return out


class BanlistRule(Rule):
    """Enforce the selected banlist version (banned, limits, choice restriction,
    group limits, conditional rules)."""

    code = "BANLIST"

    def check(self, ctx):
        if not ctx.banlist_version:
            return []
        from apps.banlists.services import banlist_violations

        return [
            self.error(v["code"], v["message"], **{k: val for k, val in v.items()
                                                   if k not in ("code", "message")})
            for v in banlist_violations(ctx.lines, ctx.banlist_version,
                                        format_code=ctx.format_code)
        ]


class CollectionWarningRule(Rule):
    """Missing owned copies → WARNING only. Never invalidates the deck."""

    code = "MISSING_OWNED_COPIES"

    def check(self, ctx):
        if not ctx.owned_map:
            return []
        per_identity: dict[str, tuple[str, int]] = {}
        for line in ctx.lines:
            name, qty = per_identity.get(line.card_uuid, (line.name, 0))
            per_identity[line.card_uuid] = (line.name, qty + line.quantity)
        out = []
        for uuid, (name, used) in per_identity.items():
            owned = ctx.owned_map.get(uuid, 0)
            if used > owned:
                out.append(self.warning(
                    "MISSING_OWNED_COPIES",
                    f"Você utiliza {used} cópias de “{name}”, mas possui {owned}.",
                    card_id=uuid, missing_quantity=used - owned,
                ))
        return out


DEFAULT_RULES: list[Rule] = [
    ZoneCountRule(), CopyLimitRule(), TriggerRule(), NationLockRule(),
    BanlistRule(), PowerPolicyRule(), CollectionWarningRule(),
]


def run_engine(ctx: ValidationContext, rules: list[Rule] | None = None) -> dict:
    rules = rules or DEFAULT_RULES
    errors, warnings = [], []
    for rule in rules:
        for issue in rule.check(ctx):
            (errors if issue["severity"] == "error" else warnings).append(
                {k: v for k, v in issue.items() if k != "severity"}
            )

    pm = ctx.power_map
    powered = [(ln, pm.get(ln.card_uuid)) for ln in ctx.lines]
    powered = [(ln, v) for ln, v in powered if v is not None]
    max_power = max((v for _, v in powered), default=None)
    power_point_total = sum(v * ln.quantity for ln, v in powered)

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "main_deck_count": ctx.zone_count("main_deck"),
            "ride_deck_count": ctx.zone_count("ride_deck"),
            "g_deck_count": ctx.zone_count("g_deck"),
            "trigger_count": ctx.trigger_count(),
            "maximum_power_level": max_power,
            "power_point_total": power_point_total,
        },
        "reference_date": (ctx.reference_date or timezone.now().date()).isoformat(),
    }
