"""Banlist enforcement.

Given deck lines and a BanlistVersion, produce structured violations. Choice
Restriction and group limits are evaluated over the real group entities.
"""
from __future__ import annotations

from django.db import transaction

from .choices import ConditionType, GroupKind, RestrictionType
from .models import Banlist, BanlistEntry, BanlistVersion, RestrictionGroup, RestrictionGroupMember


@transaction.atomic
def ensure_draft_version(banlist: Banlist) -> BanlistVersion:
    if banlist.current_version_id:
        return banlist.current_version
    version = BanlistVersion.objects.create(banlist=banlist, version=1)
    banlist.current_version = version
    banlist.save(update_fields=["current_version"])
    return version


@transaction.atomic
def fork_banlist(banlist: Banlist, user) -> Banlist:
    from .choices import BanlistCategory

    src = ensure_draft_version(banlist)
    new = Banlist.objects.create(
        name=f"{banlist.name} (fork)", description=banlist.description,
        objective=banlist.objective, format_code=banlist.format_code,
        category=BanlistCategory.COMMUNITY, owner=user, forked_from=banlist,
    )
    version = BanlistVersion.objects.create(banlist=new, version=1)
    new.current_version = version
    new.save(update_fields=["current_version"])
    # copy groups (map old→new) then entries
    group_map = {}
    for g in src.restriction_groups.all():
        ng = RestrictionGroup.objects.create(version=version, name=g.name, kind=g.kind,
                                             limit_value=g.limit_value, note=g.note)
        group_map[g.id] = ng
        for m in g.members.all():
            RestrictionGroupMember.objects.create(group=ng, card=m.card,
                                                  per_card_limit=m.per_card_limit)
    for e in src.entries.all():
        BanlistEntry.objects.create(
            version=version, restriction_type=e.restriction_type, card=e.card,
            group=group_map.get(e.group_id), limit_value=e.limit_value, note=e.note,
        )
    return new


def _aggregate(lines) -> tuple[dict, dict]:
    """Return (qty_by_card, lines_by_card) keyed by card_uuid."""
    qty: dict[str, int] = {}
    by_card: dict[str, list] = {}
    for line in lines:
        qty[line.card_uuid] = qty.get(line.card_uuid, 0) + line.quantity
        by_card.setdefault(line.card_uuid, []).append(line)
    return qty, by_card


def _condition_met(cond, lines, qty_by_card, format_code) -> bool:
    v = cond.value or {}
    if cond.condition_type == ConditionType.NATION:
        return any(ln.nation == v.get("nation") for ln in lines)
    if cond.condition_type == ConditionType.CLAN:
        wanted = v.get("clan")
        return any(getattr(ln, "clan", "") == wanted for ln in lines)
    if cond.condition_type == ConditionType.FORMAT:
        return format_code == v.get("format")
    if cond.condition_type == ConditionType.HAS_CARD:
        return qty_by_card.get(v.get("card_uuid"), 0) > 0
    return False


def banlist_violations(lines, version, *, format_code="standard") -> list[dict]:
    if version is None:
        return []
    qty_by_card, _ = _aggregate(lines)
    violations: list[dict] = []

    entries = list(
        version.entries.select_related("card", "group").prefetch_related(
            "group__members__card", "conditions"
        )
    )

    for entry in entries:
        rt = entry.restriction_type

        if rt == RestrictionType.BANNED and entry.card_id:
            uuid = str(entry.card.uuid)
            if qty_by_card.get(uuid, 0) > 0:
                violations.append({
                    "code": "BANNED_CARD", "card_id": uuid,
                    "message": f"“{entry.card.name}” é proibida pela banlist selecionada.",
                    "current_quantity": qty_by_card[uuid], "allowed_quantity": 0,
                })

        elif rt in (RestrictionType.LIMIT_TO_1, RestrictionType.LIMIT_TO_2,
                    RestrictionType.LIMIT_TO_N) and entry.card_id:
            uuid = str(entry.card.uuid)
            limit = entry.effective_limit()
            used = qty_by_card.get(uuid, 0)
            if used > limit:
                violations.append({
                    "code": "LIMIT_EXCEEDED", "card_id": uuid,
                    "message": f"“{entry.card.name}” é limitada a {limit} cópia(s) (atual: {used}).",
                    "current_quantity": used, "allowed_quantity": limit,
                })

        elif rt == RestrictionType.FIRST_VANGUARD_FORBIDDEN and entry.card_id:
            uuid = str(entry.card.uuid)
            in_ride_as_fv = any(
                ln.card_uuid == uuid and ln.zone == "ride_deck" and ln.grade == 0 for ln in lines
            )
            if in_ride_as_fv:
                violations.append({
                    "code": "FIRST_VANGUARD_FORBIDDEN", "card_id": uuid,
                    "message": f"“{entry.card.name}” não pode ser usada como First Vanguard.",
                })

        elif rt in (RestrictionType.CHOICE_RESTRICTION, RestrictionType.MAX_DISTINCT_FROM_GROUP,
                    RestrictionType.MAX_TOTAL_FROM_GROUP) and entry.group_id:
            group = entry.group
            member_uuids = [str(m.card.uuid) for m in group.members.all()]
            present = [u for u in member_uuids if qty_by_card.get(u, 0) > 0]
            total = sum(qty_by_card.get(u, 0) for u in member_uuids)
            limit = group.limit_value

            if group.kind == GroupKind.CHOICE or rt == RestrictionType.CHOICE_RESTRICTION:
                if len(present) > max(1, limit):
                    violations.append({
                        "code": "CHOICE_RESTRICTION", "group": group.name,
                        "message": f"Choice Restriction “{group.name}”: escolha no máximo "
                                   f"{max(1, limit)} entre as cartas do grupo (usadas: {len(present)}).",
                    })
            elif group.kind == GroupKind.MAX_DISTINCT:
                if len(present) > limit:
                    violations.append({
                        "code": "MAX_DISTINCT_FROM_GROUP", "group": group.name,
                        "message": f"Máximo de {limit} identidades diferentes do grupo "
                                   f"“{group.name}” (atual: {len(present)}).",
                    })
            elif group.kind == GroupKind.MAX_TOTAL:
                if total > limit:
                    violations.append({
                        "code": "MAX_TOTAL_FROM_GROUP", "group": group.name,
                        "message": f"Máximo de {limit} cópias totais do grupo "
                                   f"“{group.name}” (atual: {total}).",
                    })

        elif rt == RestrictionType.DECK_DEPENDENT_RESTRICTION and entry.card_id:
            conditions = list(entry.conditions.all())
            if conditions and all(
                _condition_met(c, lines, qty_by_card, format_code) for c in conditions
            ):
                uuid = str(entry.card.uuid)
                limit = entry.effective_limit()
                used = qty_by_card.get(uuid, 0)
                if used > limit:
                    violations.append({
                        "code": "DECK_DEPENDENT_RESTRICTION", "card_id": uuid,
                        "message": f"“{entry.card.name}” restrita a {limit} nas condições atuais "
                                   f"(atual: {used}).",
                        "current_quantity": used, "allowed_quantity": limit,
                    })
        # ALLOWED_EXCEPTION / UNRESTRICTED_HISTORY: informational, no enforcement.

    return violations
