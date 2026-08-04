"""Tournament lifecycle, deck submission, bracket generation and result reporting.

Design guarantees:
- Snapshots are immutable: locking freezes rules/banlist/power policy; submitting
  freezes the decklist (with a content hash). Later changes to the source deck or
  to global banlists never alter a locked tournament.
- Advancing a winner is idempotent: a duplicated confirm request never advances a
  bracket twice (guarded by row-level lock + the `advanced` flag).
"""
from __future__ import annotations

import hashlib
import json
import math
import secrets

from django.db import transaction
from django.utils import timezone

from apps.common.models import record_audit

from .choices import (
    BracketType,
    MatchState,
    ParticipantStatus,
    RegistrationStatus,
    RoundStatus,
    TournamentStatus,
)
from .models import (
    Tournament,
    TournamentAuditLog,
    TournamentCheckIn,
    TournamentDeckSubmission,
    TournamentMatch,
    TournamentParticipant,
    TournamentRegistration,
    TournamentRound,
    TournamentRulesSnapshot,
    TournamentStage,
    TournamentStanding,
)


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def audit(tournament, action, actor, summary="", **payload):
    TournamentAuditLog.objects.create(tournament=tournament, action=action, actor=actor,
                                      summary=summary[:255], payload=payload)
    record_audit(action="admin_action" if action not in {
        "match_result_correction", "disqualification", "bracket_change",
    } else action, actor=actor, target=tournament, summary=f"[{tournament.name}] {summary}")


# --- Lifecycle ------------------------------------------------------------
def open_registration(tournament: Tournament, actor) -> Tournament:
    tournament.status = TournamentStatus.REGISTRATION
    if tournament.visibility != "public" and not tournament.invite_code:
        tournament.invite_code = secrets.token_urlsafe(6)[:10]
    tournament.save(update_fields=["status", "invite_code"])
    audit(tournament, "registration_opened", actor, "Inscrições abertas")
    return tournament


@transaction.atomic
def register(tournament: Tournament, user, note="") -> TournamentRegistration:
    reg, created = TournamentRegistration.objects.get_or_create(
        tournament=tournament, user=user,
        defaults={"status": RegistrationStatus.APPROVED if tournament.auto_approve
                  else RegistrationStatus.PENDING, "note": note},
    )
    if created and reg.status == RegistrationStatus.APPROVED:
        _ensure_participant(tournament, user)
    return reg


def _ensure_participant(tournament, user) -> TournamentParticipant:
    p, _ = TournamentParticipant.objects.get_or_create(tournament=tournament, user=user)
    return p


def set_registration_status(reg: TournamentRegistration, status: str, actor):
    reg.status = status
    reg.save(update_fields=["status"])
    if status == RegistrationStatus.APPROVED:
        _ensure_participant(reg.tournament, reg.user)
    elif status in (RegistrationStatus.REJECTED, RegistrationStatus.WITHDRAWN):
        TournamentParticipant.objects.filter(tournament=reg.tournament, user=reg.user).delete()
    audit(reg.tournament, "registration_reviewed", actor,
          f"{reg.user.username}: {status}")


@transaction.atomic
def build_rules_snapshot(tournament: Tournament) -> TournamentRulesSnapshot:
    """Freeze the effective rules/banlist/power policy for the whole event."""
    from apps.banlists.serializers import BanlistVersionSerializer
    from apps.formats.models import GameFormat

    fmt = GameFormat.objects.filter(code=tournament.format_code).first()
    rule_version = fmt.current_version() if fmt else None
    banlist_payload = None
    if tournament.banlist and tournament.banlist.current_version:
        banlist_payload = BanlistVersionSerializer(tournament.banlist.current_version).data
        tournament.banlist_version_number = tournament.banlist.current_version.version

    payload = {
        "format_code": tournament.format_code,
        "format_rules_version": rule_version.version if rule_version else None,
        "banlist": banlist_payload,
        "power_policy": {"kind": tournament.power_policy.kind,
                         "config": tournament.power_policy.config}
        if tournament.power_policy else None,
        "custom_rules": tournament.custom_rules,
        "best_of": tournament.best_of,
        "frozen_at": timezone.now().isoformat(),
    }
    snap, _ = TournamentRulesSnapshot.objects.update_or_create(
        tournament=tournament,
        defaults={"payload": payload, "content_hash": _hash(payload)},
    )
    tournament.save(update_fields=["banlist_version_number"])
    return snap


@transaction.atomic
def lock_registration(tournament: Tournament, actor) -> Tournament:
    build_rules_snapshot(tournament)
    # Lock every submission so later deck edits can't change what was submitted.
    TournamentDeckSubmission.objects.filter(tournament=tournament).update(locked=True)
    tournament.status = TournamentStatus.CHECK_IN if tournament.requires_checkin \
        else TournamentStatus.LOCKED
    tournament.save(update_fields=["status"])
    audit(tournament, "registration_locked", actor, "Inscrições travadas + snapshots congelados")
    return tournament


def check_in(tournament: Tournament, participant: TournamentParticipant):
    TournamentCheckIn.objects.get_or_create(participant=participant)
    participant.status = ParticipantStatus.CHECKED_IN
    participant.save(update_fields=["status"])


def disqualify(participant: TournamentParticipant, actor, reason=""):
    participant.status = ParticipantStatus.DISQUALIFIED
    participant.dq_reason = reason
    participant.save(update_fields=["status", "dq_reason"])
    audit(participant.tournament, "disqualification", actor,
          f"{participant.user.username} desclassificado", reason=reason)


# --- Deck submission (immutable) -----------------------------------------
@transaction.atomic
def submit_deck(tournament: Tournament, participant: TournamentParticipant, deck, actor) \
        -> TournamentDeckSubmission:
    from apps.decks.models import DeckSnapshot
    from apps.decks.services import _serialize_entries, ensure_working_version
    from apps.validation.service import validate_deck_version

    version = ensure_working_version(deck)
    entries = _serialize_entries(version)
    banlist_version = tournament.banlist.current_version if tournament.banlist else None
    result = validate_deck_version(version, power_policy=tournament.power_policy,
                                   banlist_version=banlist_version)
    payload = {"entries": entries, "format": deck.format_code,
               "deck_title": deck.title, "submitted_at": timezone.now().isoformat()}
    content_hash = _hash(payload["entries"])

    snap = DeckSnapshot.objects.create(
        deck=deck, version_number=version.version_number, payload=payload,
        content_hash=content_hash, created_by=actor,
    )
    submission, _ = TournamentDeckSubmission.objects.update_or_create(
        tournament=tournament, participant=participant,
        defaults={"source_deck": deck, "snapshot": snap, "content_hash": content_hash,
                  "payload": payload, "validation": result, "is_valid": result["is_valid"],
                  "submitted_by": actor},
    )
    return submission


# --- Seeding + single elimination ----------------------------------------
def _seeding_order(size: int) -> list[int]:
    """Standard bracket seeding order for `size` slots (1-indexed seeds)."""
    seeds = [1]
    while len(seeds) < size:
        length = len(seeds) * 2
        seeds = [s for pair in ((x, length + 1 - x) for x in seeds) for s in pair]
    return seeds


def _active_participants(tournament: Tournament) -> list[TournamentParticipant]:
    qs = tournament.participants.exclude(status=ParticipantStatus.DISQUALIFIED)
    if tournament.requires_checkin:
        qs = qs.filter(status=ParticipantStatus.CHECKED_IN)
    return list(qs)


@transaction.atomic
def seed_participants(tournament: Tournament, order: list[str] | None = None):
    """Assign seeds. `order` = list of participant uuids for a custom seeding
    (organizer drag-and-drop); otherwise keep existing seeds or assign by join order."""
    participants = list(tournament.participants.all())
    if order:
        pos = {u: i for i, u in enumerate(order)}
        participants.sort(key=lambda p: pos.get(str(p.uuid), 10**6))
    else:
        participants.sort(key=lambda p: (p.seed or 10**6, p.created_at))
    for i, p in enumerate(participants, start=1):
        if p.seed != i:
            p.seed = i
            p.save(update_fields=["seed"])


@transaction.atomic
def generate_single_elimination(tournament: Tournament, actor) -> TournamentStage:
    if tournament.stages.exists():
        raise ValueError("Bracket já foi gerado.")
    participants = _active_participants(tournament)
    if len(participants) < 2:
        raise ValueError("São necessários ao menos 2 participantes com check-in.")

    seed_participants(tournament)
    participants = sorted(_active_participants(tournament), key=lambda p: p.seed or 10**6)
    by_seed = {p.seed: p for p in participants}
    n = len(participants)
    size = 2 ** math.ceil(math.log2(n))
    num_rounds = int(math.log2(size))
    order = _seeding_order(size)

    stage = TournamentStage.objects.create(
        tournament=tournament, kind=BracketType.SINGLE_ELIMINATION, name="Bracket",
        status=RoundStatus.ACTIVE)

    def round_name(r):
        remaining = size >> (r - 1)
        return {2: "Final", 4: "Semifinal", 8: "Quartas"}.get(remaining, f"Rodada {r}")

    rounds = [TournamentRound.objects.create(stage=stage, number=r, name=round_name(r),
              status=RoundStatus.ACTIVE if r == 1 else RoundStatus.PENDING)
              for r in range(1, num_rounds + 1)]

    # Build matches per round; link next_match pointers.
    round_matches: dict[int, list[TournamentMatch]] = {}
    for r in range(num_rounds, 0, -1):
        count = size >> r
        round_matches[r] = [
            TournamentMatch(round=rounds[r - 1], position=p, best_of=tournament.best_of)
            for p in range(count)
        ]
        TournamentMatch.objects.bulk_create(round_matches[r])
        round_matches[r] = list(rounds[r - 1].matches.order_by("position"))

    for r in range(1, num_rounds):
        for m in round_matches[r]:
            nxt = round_matches[r + 1][m.position // 2]
            m.next_match = nxt
            m.next_slot = "a" if m.position % 2 == 0 else "b"
    # Round 1 seeding
    for i, m in enumerate(round_matches[1]):
        sa, sb = order[i * 2], order[i * 2 + 1]
        m.participant_a = by_seed.get(sa)
        m.participant_b = by_seed.get(sb)
    TournamentMatch.objects.bulk_update(
        [m for ms in round_matches.values() for m in ms],
        ["next_match", "next_slot", "participant_a", "participant_b"])

    tournament.status = TournamentStatus.RUNNING
    tournament.save(update_fields=["status"])
    audit(tournament, "bracket_generated", actor,
          f"Single elimination · {n} participantes · {num_rounds} rodadas")

    # Auto-resolve byes in round 1.
    for m in round_matches[1]:
        m.refresh_from_db()
        if m.participant_a and not m.participant_b:
            _finalize_match(m, m.participant_a, actor, state=MatchState.BYE, is_bye=True)
        elif m.participant_b and not m.participant_a:
            _finalize_match(m, m.participant_b, actor, state=MatchState.BYE, is_bye=True)
    return stage


# --- Reporting + advancing (idempotent) ----------------------------------
def _winner_from_scores(match, score_a, score_b):
    if score_a > score_b:
        return match.participant_a
    if score_b > score_a:
        return match.participant_b
    return None


@transaction.atomic
def report_result(match_uuid: str, reporter, score_a: int, score_b: int) -> TournamentMatch:
    match = TournamentMatch.objects.select_for_update().get(uuid=match_uuid)
    if match.state == MatchState.DONE:
        return match  # already settled; ignore
    winner = _winner_from_scores(match, score_a, score_b)
    match.score_a, match.score_b = score_a, score_b
    match.reported_by = reporter
    match.state = MatchState.REPORTED
    match.save(update_fields=["score_a", "score_b", "reported_by", "state"])
    from .models import MatchReport
    MatchReport.objects.create(match=match, reporter=reporter, score_a=score_a,
                               score_b=score_b, winner=winner)
    return match


@transaction.atomic
def confirm_result(match_uuid: str, confirmer, *, force=False) -> TournamentMatch:
    """Confirm a reported result → settle + advance. Idempotent: a second call on
    an already-settled match is a no-op (never advances the bracket twice)."""
    match = TournamentMatch.objects.select_for_update().get(uuid=match_uuid)
    if match.state == MatchState.DONE:
        return match
    if match.state != MatchState.REPORTED and not force:
        raise ValueError("Nenhum resultado reportado para confirmar.")
    winner = _winner_from_scores(match, match.score_a, match.score_b)
    allow_draw = match.round.stage.kind in (BracketType.SWISS, BracketType.SWISS_TOP_CUT,
                                            BracketType.ROUND_ROBIN)
    if winner is None and not (force or allow_draw):
        raise ValueError("Empate não pode ser confirmado em eliminação simples.")
    _finalize_match(match, winner, confirmer, state=MatchState.DONE)
    return match


@transaction.atomic
def organizer_set_result(match_uuid: str, organizer, score_a, score_b) -> TournamentMatch:
    """Organizer force-sets a result (correction/override), with audit."""
    match = TournamentMatch.objects.select_for_update().get(uuid=match_uuid)
    was_done = match.state == MatchState.DONE
    match.score_a, match.score_b = score_a, score_b
    winner = _winner_from_scores(match, score_a, score_b)
    match.save(update_fields=["score_a", "score_b"])
    _finalize_match(match, winner, organizer, state=MatchState.DONE, re_advance=was_done)
    audit(match.round.stage.tournament, "match_result_correction", organizer,
          f"Resultado ajustado: {score_a}-{score_b}", match=str(match.uuid))
    return match


def _finalize_match(match, winner, actor, *, state=MatchState.DONE, is_bye=False, re_advance=False):
    match.winner = winner
    match.state = state
    match.is_draw = (winner is None and state == MatchState.DONE)
    match.confirmed_by = actor if not is_bye else None
    match.save(update_fields=["winner", "state", "is_draw", "confirmed_by"])

    # Advance winner into the next match slot (idempotent).
    if match.next_match_id and winner and (not match.advanced or re_advance):
        nxt = TournamentMatch.objects.select_for_update().get(pk=match.next_match_id)
        setattr(nxt, "participant_a" if match.next_slot == "a" else "participant_b", winner)
        nxt.save(update_fields=["participant_a", "participant_b"])
        match.advanced = True
        match.save(update_fields=["advanced"])

    # Drop the loser into the losers bracket (double elimination).
    loser = None
    if winner and match.participant_a_id and match.participant_b_id:
        loser = match.participant_b if winner.id == match.participant_a_id else match.participant_a
    if match.loser_next_match_id and loser and not match.loser_advanced:
        lnx = TournamentMatch.objects.select_for_update().get(pk=match.loser_next_match_id)
        setattr(lnx, "participant_a" if match.loser_next_slot == "a" else "participant_b", loser)
        lnx.save(update_fields=["participant_a", "participant_b"])
        match.loser_advanced = True
        match.save(update_fields=["loser_advanced"])

    _maybe_complete_round(match.round)
    _recompute_standings(match.round.stage.tournament)


def _maybe_complete_round(round_obj):
    if round_obj.matches.exclude(state__in=[MatchState.DONE, MatchState.BYE]).exists():
        return
    round_obj.status = RoundStatus.COMPLETED
    round_obj.save(update_fields=["status"])

    stage = round_obj.stage
    tournament = stage.tournament

    # Swiss / Swiss+Top Cut: generate the next round (or Top Cut / finish).
    if stage.kind in (BracketType.SWISS, BracketType.SWISS_TOP_CUT):
        from .formats import advance_swiss
        advance_swiss(tournament, None)
        return

    # Round robin: activate the next pre-created round; finish when none remain.
    if stage.kind == BracketType.ROUND_ROBIN:
        nxt = stage.rounds.filter(number=round_obj.number + 1).first()
        if nxt:
            nxt.status = RoundStatus.ACTIVE
            nxt.save(update_fields=["status"])
        elif tournament.status != TournamentStatus.FINISHED:
            tournament.status = TournamentStatus.FINISHED
            tournament.save(update_fields=["status"])
        return

    # Elimination (single/double/top-cut): activate next round + auto-byes.
    nxt = stage.rounds.filter(number__gt=round_obj.number).order_by("number").first()
    if nxt:
        nxt.status = RoundStatus.ACTIVE
        nxt.save(update_fields=["status"])
        for m in nxt.matches.all():
            if m.state == MatchState.PENDING:
                if m.participant_a and not m.participant_b:
                    _finalize_match(m, m.participant_a, None, state=MatchState.BYE, is_bye=True)
                elif m.participant_b and not m.participant_a:
                    _finalize_match(m, m.participant_b, None, state=MatchState.BYE, is_bye=True)
    elif not stage.rounds.exclude(status=RoundStatus.COMPLETED).exists():
        if tournament.status != TournamentStatus.FINISHED:
            tournament.status = TournamentStatus.FINISHED
            tournament.save(update_fields=["status"])


# --- Standings ------------------------------------------------------------
def compute_swiss_standings(tournament: Tournament) -> list[dict]:
    """Match points + tiebreakers (OMW%, GW%, OGW%) — TCG-standard for Swiss."""
    parts = list(tournament.participants.all())
    matches = list(TournamentMatch.objects.filter(
        round__stage__tournament=tournament,
        state__in=[MatchState.DONE, MatchState.BYE]).select_related("round__stage"))

    mp, mw, ml, md = {}, {}, {}, {}     # match points, wins, losses, draws
    gw, gp = {}, {}                     # game wins, games played
    opponents: dict[int, list[int]] = {p.id: [] for p in parts}
    for p in parts:
        mp[p.id] = mw[p.id] = ml[p.id] = md[p.id] = gw[p.id] = gp[p.id] = 0

    for m in matches:
        a, b = m.participant_a_id, m.participant_b_id
        if a:
            gp[a] = gp.get(a, 0) + m.score_a + m.score_b
            gw[a] = gw.get(a, 0) + m.score_a
        if b:
            gp[b] = gp.get(b, 0) + m.score_a + m.score_b
            gw[b] = gw.get(b, 0) + m.score_b
        if a and b:
            opponents[a].append(b)
            opponents[b].append(a)
        if m.is_draw:
            for x in (a, b):
                if x:
                    mp[x] += 1
                    md[x] += 1
        elif m.winner_id:
            loser = b if m.winner_id == a else a
            mp[m.winner_id] += 3
            mw[m.winner_id] += 1
            if loser:
                ml[loser] += 1

    def mwp(pid):  # match-win %, floored at 1/3
        played = mw[pid] + ml[pid] + md[pid]
        return max(mp[pid] / (3 * played), 1 / 3) if played else 1 / 3

    def gwp(pid):
        return max(gw[pid] / gp[pid], 1 / 3) if gp.get(pid) else 1 / 3

    def omw(pid):
        opps = opponents[pid]
        return sum(mwp(o) for o in opps) / len(opps) if opps else 0

    def ogw(pid):
        opps = opponents[pid]
        return sum(gwp(o) for o in opps) / len(opps) if opps else 0

    rows = [{
        "participant": p, "points": mp[p.id], "wins": mw[p.id], "losses": ml[p.id],
        "draws": md[p.id],
        "tiebreaks": {"omw": round(omw(p.id), 4), "gw": round(gwp(p.id), 4),
                      "ogw": round(ogw(p.id), 4)},
    } for p in parts]
    rows.sort(key=lambda r: (-r["points"], -r["tiebreaks"]["omw"],
                             -r["tiebreaks"]["gw"], -r["tiebreaks"]["ogw"]))
    return rows


def _recompute_standings(tournament: Tournament):
    stage = tournament.stages.first()
    if not stage:
        return
    if stage.kind in (BracketType.SWISS, BracketType.SWISS_TOP_CUT, BracketType.ROUND_ROBIN):
        # Only the Swiss/RR stage drives standings (Top Cut elim results shown on bracket).
        rows = compute_swiss_standings(tournament)
        TournamentStanding.objects.filter(tournament=tournament).delete()
        objs = []
        for i, r in enumerate(rows, start=1):
            objs.append(TournamentStanding(
                tournament=tournament, participant=r["participant"], rank=i,
                wins=r["wins"], losses=r["losses"], draws=r["draws"],
                points=r["points"], tiebreaks=r["tiebreaks"]))
            p = r["participant"]
            p.wins, p.losses = r["wins"], r["losses"]
            p.final_rank = i if tournament.status == TournamentStatus.FINISHED else None
        TournamentStanding.objects.bulk_create(objs)
        TournamentParticipant.objects.bulk_update(
            [r["participant"] for r in rows], ["wins", "losses", "final_rank"])
        return
    _recompute_elim_standings(tournament, stage)


def _recompute_elim_standings(tournament, stage):
    """Rank by elimination depth for single/double elimination."""
    matches = list(TournamentMatch.objects.filter(round__stage=stage).select_related("round"))
    max_round = max((m.round.number for m in matches), default=0)

    # wins/losses per participant + the round they were eliminated in.
    elim_round: dict[int, int] = {}
    wins: dict[int, int] = {}
    losses: dict[int, int] = {}
    for m in matches:
        if m.state not in (MatchState.DONE, MatchState.BYE) or not m.winner_id:
            continue
        loser = m.participant_b_id if m.winner_id == m.participant_a_id else m.participant_a_id
        wins[m.winner_id] = wins.get(m.winner_id, 0) + (0 if m.state == MatchState.BYE else 1)
        if loser:
            losses[loser] = losses.get(loser, 0) + 1
            elim_round[loser] = m.round.number

    champion = None
    final_match = next((m for m in matches if m.round.number == max_round), None)
    if final_match and final_match.state == MatchState.DONE and final_match.winner_id:
        champion = final_match.winner_id

    participants = list(tournament.participants.all())

    def rank_key(p):
        if p.id == champion:
            return (0, 0)
        er = elim_round.get(p.id, 0)
        return (max_round - er + 1, -(wins.get(p.id, 0)))

    ordered = sorted(participants, key=rank_key)
    TournamentStanding.objects.filter(tournament=tournament).delete()
    rows = []
    for i, p in enumerate(ordered, start=1):
        w, ls = wins.get(p.id, 0), losses.get(p.id, 0)
        rows.append(TournamentStanding(tournament=tournament, participant=p, rank=i,
                                       wins=w, losses=ls, points=w * 3))
        p.wins, p.losses, p.final_rank = w, ls, (i if tournament.status == TournamentStatus.FINISHED else None)
    TournamentStanding.objects.bulk_create(rows)
    TournamentParticipant.objects.bulk_update(participants, ["wins", "losses", "final_rank"])
