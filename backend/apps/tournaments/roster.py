"""Roster championship — building, validation, power assignment and locking.

The tournament OWNER assigns each deck's `power`; the sum across a participant's
roster must stay within `tournament.power_cap`. Adding decks (player) validates
count + banlist; assigning power (owner) recomputes the cap and validity. Locking
freezes an immutable DeckSnapshot per roster deck so later deck edits never change
what was registered.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from .choices import RosterStatus
from .models import RosterDeck, TournamentRoster
from .services import audit


def get_or_create_roster(tournament, participant) -> TournamentRoster:
    roster, _ = TournamentRoster.objects.get_or_create(tournament=tournament, participant=participant)
    return roster


def _banlist_check(tournament, deck) -> tuple[bool, dict]:
    """Validate a deck against the tournament banlist. If the tournament has no
    banlist, banlist validation is skipped (always valid)."""
    from apps.decks.services import ensure_working_version
    from apps.validation.service import validate_deck_version

    version = ensure_working_version(deck)
    banlist_version = tournament.banlist.current_version if tournament.banlist_id else None
    result = validate_deck_version(version, banlist_version=banlist_version)
    return result["is_valid"], result


@transaction.atomic
def add_roster_deck(tournament, participant, deck, actor) -> RosterDeck:
    """Player adds a deck to their roster. Validates deck count and banlist.
    Power is NOT set here — the owner assigns it later."""
    roster = get_or_create_roster(tournament, participant)
    if roster.status == RosterStatus.LOCKED:
        raise ValueError("Roster travado — não é possível alterar.")
    existing = list(roster.decks.all())
    if any(rd.source_deck_id == deck.id for rd in existing):
        raise ValueError("Deck já está no roster.")
    if len(existing) >= tournament.decks_per_player:
        raise ValueError(f"O roster comporta no máximo {tournament.decks_per_player} decks.")

    banlist_valid, validation = _banlist_check(tournament, deck)
    rd = RosterDeck.objects.create(
        roster=roster, source_deck=deck, label=deck.title,
        power=deck.power_stars,  # deck owner's self-rating as a suggested default
        power_by=None,
        banlist_valid=banlist_valid, validation=validation,
        slot=len(existing), order_index=len(existing),
    )
    recompute_roster(roster)
    audit(tournament, "roster_deck_added", actor, f"{participant.user.username}: +{deck.title}",
          deck=str(deck.uuid))
    return rd


@transaction.atomic
def remove_roster_deck(roster_deck, actor) -> TournamentRoster:
    roster = roster_deck.roster
    if roster.status == RosterStatus.LOCKED or roster_deck.locked:
        raise ValueError("Roster travado — não é possível alterar.")
    tournament = roster.tournament
    label = roster_deck.label
    roster_deck.delete()
    recompute_roster(roster)
    audit(tournament, "roster_deck_removed", actor,
          f"{roster.participant.user.username}: -{label}")
    return roster


@transaction.atomic
def set_deck_power(roster_deck, power, actor) -> RosterDeck:
    """Owner assigns a deck's power (the cap unit). Validates min/max and
    recomputes the roster; the caller is expected to be the organizer."""
    tournament = roster_deck.roster.tournament
    if roster_deck.locked or roster_deck.roster.status == RosterStatus.LOCKED:
        raise ValueError("Roster travado — poder não pode mais ser alterado.")
    if power is not None:
        lo = tournament.min_deck_power
        hi = tournament.max_deck_power
        if lo is not None and power < lo:
            raise ValueError(f"Poder mínimo por deck é {lo}.")
        if hi is not None and power > hi:
            raise ValueError(f"Poder máximo por deck é {hi}.")
    was_valid = roster_deck.roster.status in (RosterStatus.VALID, RosterStatus.CONFIRMED)
    roster_deck.power = power
    roster_deck.power_by = actor
    roster_deck.save(update_fields=["power", "power_by"])
    roster = recompute_roster(roster_deck.roster)
    audit(tournament, "roster_power_set", actor,
          f"{roster.participant.user.username} · {roster_deck.label}: poder {power}",
          roster_deck=str(roster_deck.uuid), power=power)
    # Flag the player if the change just invalidated a previously valid roster.
    if was_valid and roster.status == RosterStatus.INVALID:
        audit(tournament, "roster_invalidated", actor,
              f"Roster de {roster.participant.user.username} ficou inválido "
              f"({roster.power_used}/{tournament.power_cap}).")
    return roster_deck


@transaction.atomic
def set_ace(roster, roster_deck, actor) -> TournamentRoster:
    """Mark exactly one roster deck as the Ace (or clear if roster_deck is None)."""
    tournament = roster.tournament
    if not tournament.ace_enabled:
        raise ValueError("Ace Deck não está ativado neste campeonato.")
    if roster.status == RosterStatus.LOCKED:
        raise ValueError("Roster travado — o Ace não pode mais ser alterado.")
    roster.decks.update(is_ace=False)
    if roster_deck is not None:
        if roster_deck.roster_id != roster.id:
            raise ValueError("Deck não pertence a este roster.")
        roster_deck.is_ace = True
        roster_deck.save(update_fields=["is_ace"])
    recompute_roster(roster)
    audit(tournament, "roster_ace_set", actor,
          f"{roster.participant.user.username} · Ace: "
          f"{roster_deck.label if roster_deck else 'nenhum'}")
    return roster


def recompute_roster(roster) -> TournamentRoster:
    """Recompute power_used / over-cap / per-deck validity / roster status.
    Does not change a LOCKED roster's status."""
    tournament = roster.tournament
    decks = list(roster.decks.all())
    power_used = sum(rd.power or 0 for rd in decks)
    over_cap = power_used > tournament.power_cap

    for rd in decks:
        rd_valid = (
            rd.banlist_valid
            and rd.power is not None
            and (tournament.min_deck_power is None or rd.power >= tournament.min_deck_power)
            and (tournament.max_deck_power is None or rd.power <= tournament.max_deck_power)
        )
        if rd.is_valid != rd_valid:
            rd.is_valid = rd_valid
            rd.save(update_fields=["is_valid"])

    complete = len(decks) == tournament.decks_per_player
    ace_ok = (not tournament.ace_enabled) or (not tournament.ace_required) or any(rd.is_ace for rd in decks)
    all_valid = complete and not over_cap and all(rd.is_valid for rd in decks) and ace_ok

    roster.power_used = power_used
    roster.is_over_cap = over_cap
    if roster.status != RosterStatus.LOCKED:
        if roster.status == RosterStatus.CONFIRMED and all_valid:
            new_status = RosterStatus.CONFIRMED
        elif all_valid:
            new_status = RosterStatus.VALID
        elif not decks:
            new_status = RosterStatus.DRAFT
        else:
            new_status = RosterStatus.INVALID
        roster.status = new_status
    roster.save(update_fields=["power_used", "is_over_cap", "status"])
    return roster


@transaction.atomic
def confirm_roster(roster, actor) -> TournamentRoster:
    roster = recompute_roster(roster)
    tournament = roster.tournament
    if len(roster.decks.all()) != tournament.decks_per_player:
        raise ValueError(f"Selecione exatamente {tournament.decks_per_player} decks.")
    if roster.is_over_cap:
        raise ValueError(f"Roster acima do cap ({roster.power_used}/{tournament.power_cap}).")
    if not all(rd.is_valid for rd in roster.decks.all()):
        raise ValueError("Há decks inválidos no roster (banlist ou poder não definido).")
    if tournament.ace_enabled and tournament.ace_required and not roster.decks.filter(is_ace=True).exists():
        raise ValueError("Escolha um Ace antes de confirmar.")
    roster.status = RosterStatus.CONFIRMED
    roster.confirmed_at = timezone.now()
    roster.save(update_fields=["status", "confirmed_at"])
    audit(tournament, "roster_confirmed", actor, f"{roster.participant.user.username} confirmou o roster")
    return roster


def roster_standings(tournament) -> list[dict]:
    """Per-participant standings enriched with roster stats: points/record,
    Ace wins, penalties, and a per-deck win-rate breakdown. Ordered by points,
    then (when the Ace-tiebreak rule is on) Ace wins, then wins."""
    from .choices import MatchState
    from .models import TournamentMatch, TournamentPenalty, TournamentStanding

    parts = list(tournament.participants.select_related("user__profile").all())
    base = {s.participant_id: s for s in
            TournamentStanding.objects.filter(tournament=tournament)}
    pen = {}
    for p in TournamentPenalty.objects.filter(participant__tournament=tournament):
        pen[p.participant_id] = pen.get(p.participant_id, 0) + p.points

    deck_rec: dict[int, dict] = {}
    ace_wins: dict[int, int] = {}
    matches = (TournamentMatch.objects
               .filter(round__stage__tournament=tournament, state=MatchState.DONE)
               .prefetch_related("deck_selections__roster_deck"))
    for m in matches:
        sels = {s.participant_id: s for s in m.deck_selections.all()}
        for pid, sel in sels.items():
            if not sel.roster_deck_id:
                continue
            rec = deck_rec.setdefault(sel.roster_deck_id, {"wins": 0, "losses": 0})
            won = m.winner_id == pid
            rec["wins" if won else "losses"] += 1
            if won and (sel.is_ace_used or (sel.roster_deck and sel.roster_deck.is_ace)):
                ace_wins[pid] = ace_wins.get(pid, 0) + 1

    rows = []
    for p in parts:
        st = base.get(p.id)
        roster = getattr(p, "roster", None)
        decks = []
        if roster:
            for rd in roster.decks.all():
                rec = deck_rec.get(rd.id, {"wins": 0, "losses": 0})
                games = rec["wins"] + rec["losses"]
                decks.append({
                    "label": rd.label, "is_ace": rd.is_ace, "power": rd.power,
                    "wins": rec["wins"], "losses": rec["losses"], "games": games,
                    "win_rate": round(rec["wins"] / games, 2) if games else None,
                })
        rows.append({
            "participant": {"uuid": str(p.uuid), "username": p.user.username,
                            "avatar_key": getattr(getattr(p.user, "profile", None), "avatar_key", "")},
            "points": (st.points if st else 0) + pen.get(p.id, 0),
            "wins": st.wins if st else p.wins, "losses": st.losses if st else p.losses,
            "draws": st.draws if st else p.draws,
            "ace_wins": ace_wins.get(p.id, 0),
            "penalties": pen.get(p.id, 0),
            "decks": decks,
        })

    ace_tiebreak = tournament.ace_enabled and tournament.ace_rule == "tiebreak_wins"
    rows.sort(key=lambda r: (-r["points"], -(r["ace_wins"] if ace_tiebreak else 0), -r["wins"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    return rows


@transaction.atomic
def lock_rosters(tournament, actor=None):
    """Freeze every roster deck as an immutable DeckSnapshot and lock the rosters.
    Called at registration lock for roster-kind tournaments."""
    from apps.decks.models import DeckSnapshot
    from apps.decks.services import _serialize_entries, ensure_working_version, snapshot_hash

    for roster in tournament.rosters.select_related("participant").all():
        for rd in roster.decks.select_related("source_deck").all():
            if rd.snapshot_id or not rd.source_deck_id:
                continue
            version = ensure_working_version(rd.source_deck)
            payload = {"entries": _serialize_entries(version), "deck_title": rd.source_deck.title}
            snap = DeckSnapshot.objects.create(
                deck=rd.source_deck, version_number=version.version_number,
                payload=payload, content_hash=snapshot_hash(version), created_by=actor,
            )
            rd.snapshot = snap
            rd.locked = True
            rd.save(update_fields=["snapshot", "locked"])
        roster.status = RosterStatus.LOCKED
        roster.save(update_fields=["status"])
    # Freeze predetermined draw sequences (no-op for other modes).
    from .selection import build_predetermined_sequences
    build_predetermined_sequences(tournament, actor)
    audit(tournament, "rosters_locked", actor, "Rosters congelados (snapshots + poder)")
