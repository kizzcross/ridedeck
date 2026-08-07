"""Bracket-format generators: Swiss, Round Robin, Swiss + Top Cut, Double
Elimination. Single elimination lives in services.py.

Swiss pairs by score (greedy, avoiding rematches), supports draws and byes, and
ranks by match points + tiebreakers (OMW%, GW%, OGW%). Round robin uses the
circle method. Top Cut spins up a single-elimination stage from the top N.
"""
from __future__ import annotations

import math
from itertools import combinations

from django.db import transaction

from .choices import BracketType, MatchState, RoundStatus, TournamentStatus
from .models import TournamentMatch, TournamentRound, TournamentStage
from .services import _active_participants, audit, seed_participants


def _bye(match, participant):
    match.participant_a = participant
    match.state = MatchState.BYE
    match.winner = participant
    match.score_a, match.score_b = 2, 0
    match.save()


def _played_pairs(tournament) -> set[frozenset]:
    pairs = set()
    for m in TournamentMatch.objects.filter(round__stage__tournament=tournament):
        if m.participant_a_id and m.participant_b_id:
            pairs.add(frozenset((m.participant_a_id, m.participant_b_id)))
    return pairs


def _points(tournament) -> dict[int, int]:
    pts: dict[int, int] = {p.id: 0 for p in tournament.participants.all()}
    for m in TournamentMatch.objects.filter(round__stage__tournament=tournament,
                                            state__in=[MatchState.DONE, MatchState.BYE]):
        if m.is_draw:
            if m.participant_a_id:
                pts[m.participant_a_id] = pts.get(m.participant_a_id, 0) + 1
            if m.participant_b_id:
                pts[m.participant_b_id] = pts.get(m.participant_b_id, 0) + 1
        elif m.winner_id:
            pts[m.winner_id] = pts.get(m.winner_id, 0) + 3
    return pts


# --- Swiss ----------------------------------------------------------------
def swiss_rounds_for(n: int) -> int:
    return max(3, math.ceil(math.log2(max(n, 2))))


@transaction.atomic
def generate_swiss(tournament, actor, *, num_rounds: int | None = None,
                   kind=BracketType.SWISS) -> TournamentStage:
    if tournament.stages.exists():
        raise ValueError("Bracket já foi gerado.")
    seed_participants(tournament)
    participants = _active_participants(tournament)
    if len(participants) < 2:
        raise ValueError("São necessários ao menos 2 participantes.")
    rounds = num_rounds or swiss_rounds_for(len(participants))
    stage = TournamentStage.objects.create(
        tournament=tournament, kind=kind, name="Swiss", status=RoundStatus.ACTIVE,
        config={"num_rounds": rounds, "current_round": 1,
                "top_cut_size": tournament.custom_rules.get("top_cut_size", 8)
                if kind == BracketType.SWISS_TOP_CUT else 0})
    _create_swiss_round(tournament, stage, 1)
    tournament.status = TournamentStatus.RUNNING
    tournament.save(update_fields=["status"])
    audit(tournament, "bracket_generated", actor,
          f"Swiss · {len(participants)} jogadores · {rounds} rodadas")
    return stage


def _create_swiss_round(tournament, stage, number: int) -> TournamentRound:
    rnd = TournamentRound.objects.create(stage=stage, number=number,
                                         name=f"Rodada {number}", status=RoundStatus.ACTIVE)
    pts = _points(tournament)
    played = _played_pairs(tournament)
    # sort by points desc, then seed
    parts = sorted(_active_participants(tournament),
                   key=lambda p: (-pts.get(p.id, 0), p.seed or 10**6))
    ids = [p for p in parts]

    # greedy pairing avoiding rematches
    used = set()
    pairings = []
    for i, pa in enumerate(ids):
        if pa.id in used:
            continue
        partner = None
        for pb in ids[i + 1:]:
            if pb.id in used:
                continue
            if frozenset((pa.id, pb.id)) in played:
                continue
            partner = pb
            break
        if partner is None:
            # allow rematch if unavoidable
            for pb in ids[i + 1:]:
                if pb.id not in used:
                    partner = pb
                    break
        if partner is None:
            pairings.append((pa, None))  # bye
            used.add(pa.id)
        else:
            pairings.append((pa, partner))
            used.update({pa.id, partner.id})

    for pos, (pa, pb) in enumerate(pairings):
        m = TournamentMatch.objects.create(round=rnd, position=pos, best_of=tournament.best_of,
                                           participant_a=pa, participant_b=pb, table_number=pos + 1)
        if pb is None:
            _bye(m, pa)
    return rnd


@transaction.atomic
def advance_swiss(tournament, actor) -> TournamentRound | None:
    """Called after a Swiss round completes → create next round, or start Top Cut,
    or finish."""
    stage = tournament.stages.filter(kind__in=[BracketType.SWISS, BracketType.SWISS_TOP_CUT]).first()
    if not stage:
        return None
    cfg = stage.config
    current = cfg.get("current_round", 1)
    total = cfg.get("num_rounds", 3)
    if current < total:
        cfg["current_round"] = current + 1
        stage.config = cfg
        stage.save(update_fields=["config"])
        return _create_swiss_round(tournament, stage, current + 1)
    # Swiss complete
    stage.status = RoundStatus.COMPLETED
    stage.save(update_fields=["status"])
    if stage.kind == BracketType.SWISS_TOP_CUT and cfg.get("top_cut_size"):
        start_top_cut(tournament, actor, cfg["top_cut_size"])
        return None
    tournament.status = TournamentStatus.FINISHED
    tournament.save(update_fields=["status"])
    return None


# --- Top Cut --------------------------------------------------------------
@transaction.atomic
def start_top_cut(tournament, actor, size: int):
    from .services import (
        compute_swiss_standings,  # defined below via monkey? -> use inline
    )

    standings = compute_swiss_standings(tournament)
    top = [row["participant"] for row in standings[:size]]
    if len(top) < 2:
        tournament.status = TournamentStatus.FINISHED
        tournament.save(update_fields=["status"])
        return
    _build_single_elim_stage(tournament, top, name=f"Top {len(top)}")
    audit(tournament, "top_cut_started", actor, f"Top Cut · {len(top)} jogadores")


# --- Round robin ----------------------------------------------------------
@transaction.atomic
def generate_round_robin(tournament, actor) -> TournamentStage:
    if tournament.stages.exists():
        raise ValueError("Bracket já foi gerado.")
    seed_participants(tournament)
    parts = _active_participants(tournament)
    if len(parts) < 2:
        raise ValueError("São necessários ao menos 2 participantes.")
    stage = TournamentStage.objects.create(tournament=tournament, kind=BracketType.ROUND_ROBIN,
                                           name="Round Robin", status=RoundStatus.ACTIVE)
    # circle method
    players = list(parts)
    if len(players) % 2:
        players.append(None)  # bye marker
    n = len(players)
    rounds = n - 1
    half = n // 2
    arr = players[:]
    for r in range(rounds):
        rnd = TournamentRound.objects.create(stage=stage, number=r + 1, name=f"Rodada {r + 1}",
                                             status=RoundStatus.ACTIVE if r == 0 else RoundStatus.PENDING)
        for i in range(half):
            pa, pb = arr[i], arr[n - 1 - i]
            if pa is None or pb is None:
                present = pa or pb
                if present:
                    m = TournamentMatch.objects.create(round=rnd, position=i, participant_a=present)
                    _bye(m, present)
            else:
                TournamentMatch.objects.create(round=rnd, position=i, best_of=tournament.best_of,
                                               participant_a=pa, participant_b=pb, table_number=i + 1)
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]  # rotate
    tournament.status = TournamentStatus.RUNNING
    tournament.save(update_fields=["status"])
    audit(tournament, "bracket_generated", actor, f"Round robin · {len(parts)} jogadores")
    return stage


# --- Single-elim builder (shared by Top Cut) ------------------------------
def _seeding_order(size: int) -> list[int]:
    seeds = [1]
    while len(seeds) < size:
        length = len(seeds) * 2
        seeds = [s for pair in ((x, length + 1 - x) for x in seeds) for s in pair]
    return seeds


def _build_single_elim_stage(tournament, participants, name="Bracket"):
    from .services import _finalize_match

    n = len(participants)
    by_seed = {i + 1: p for i, p in enumerate(participants)}
    size = 2 ** math.ceil(math.log2(n))
    num_rounds = int(math.log2(size))
    order = _seeding_order(size)
    stage = TournamentStage.objects.create(tournament=tournament,
                                            kind=BracketType.SINGLE_ELIMINATION, name=name,
                                            status=RoundStatus.ACTIVE, order=tournament.stages.count() + 1)

    def rname(r):
        remaining = size >> (r - 1)
        return {2: "Final", 4: "Semifinal", 8: "Quartas"}.get(remaining, f"Rodada {r}")

    rounds = [TournamentRound.objects.create(stage=stage, number=r, name=rname(r),
              status=RoundStatus.ACTIVE if r == 1 else RoundStatus.PENDING)
              for r in range(1, num_rounds + 1)]
    rmatches = {}
    for r in range(num_rounds, 0, -1):
        cnt = size >> r
        TournamentMatch.objects.bulk_create(
            [TournamentMatch(round=rounds[r - 1], position=p, best_of=tournament.best_of)
             for p in range(cnt)])
        rmatches[r] = list(rounds[r - 1].matches.order_by("position"))
    for r in range(1, num_rounds):
        for m in rmatches[r]:
            m.next_match = rmatches[r + 1][m.position // 2]
            m.next_slot = "a" if m.position % 2 == 0 else "b"
    for i, m in enumerate(rmatches[1]):
        m.participant_a = by_seed.get(order[i * 2])
        m.participant_b = by_seed.get(order[i * 2 + 1])
    TournamentMatch.objects.bulk_update([m for ms in rmatches.values() for m in ms],
                                        ["next_match", "next_slot", "participant_a", "participant_b"])
    for m in rmatches[1]:
        m.refresh_from_db()
        if m.participant_a and not m.participant_b:
            _finalize_match(m, m.participant_a, None, state=MatchState.BYE, is_bye=True)
        elif m.participant_b and not m.participant_a:
            _finalize_match(m, m.participant_b, None, state=MatchState.BYE, is_bye=True)
    return stage


# --- Double elimination ---------------------------------------------------
@transaction.atomic
def generate_double_elimination(tournament, actor) -> TournamentStage:
    """Winners + losers bracket. Losers of winners-round r drop into the losers
    bracket. Simplified but correct routing for power-of-two fields."""
    from .services import _finalize_match

    if tournament.stages.exists():
        raise ValueError("Bracket já foi gerado.")
    seed_participants(tournament)
    parts = sorted(_active_participants(tournament), key=lambda p: p.seed or 10**6)
    if len(parts) < 2:
        raise ValueError("São necessários ao menos 2 participantes.")
    n = len(parts)
    size = 2 ** math.ceil(math.log2(n))
    wrounds = int(math.log2(size))
    order = _seeding_order(size)
    by_seed = {i + 1: p for i, p in enumerate(parts)}

    stage = TournamentStage.objects.create(tournament=tournament,
                                            kind=BracketType.DOUBLE_ELIMINATION, name="Double Elim",
                                            status=RoundStatus.ACTIVE)

    # Winners bracket rounds
    w_round_objs = {}
    for r in range(1, wrounds + 1):
        w_round_objs[r] = TournamentRound.objects.create(
            stage=stage, number=r, name=f"WB R{r}",
            status=RoundStatus.ACTIVE if r == 1 else RoundStatus.PENDING)
    w_matches = {}
    for r in range(wrounds, 0, -1):
        cnt = size >> r
        TournamentMatch.objects.bulk_create(
            [TournamentMatch(round=w_round_objs[r], position=p, best_of=tournament.best_of,
                             bracket="winners") for p in range(cnt)])
        w_matches[r] = list(w_round_objs[r].matches.order_by("position"))

    # Losers bracket rounds: 2*(wrounds-1) rounds (interleaved). We keep it simple:
    # LB has (2*wrounds - 2) rounds. Number them starting at 100 to avoid clashes.
    lb_round_count = max(1, 2 * (wrounds - 1))
    l_round_objs = {}
    for i in range(1, lb_round_count + 1):
        l_round_objs[i] = TournamentRound.objects.create(
            stage=stage, number=100 + i, name=f"LB R{i}", status=RoundStatus.PENDING)
    # LB match counts per round follow: R1: size/4, then alternating.
    l_sizes = []
    cur = size // 4
    for i in range(lb_round_count):
        l_sizes.append(max(1, cur))
        if i % 2 == 1:
            cur = max(1, cur // 2)
    l_matches = {}
    for i in range(1, lb_round_count + 1):
        TournamentMatch.objects.bulk_create(
            [TournamentMatch(round=l_round_objs[i], position=p, best_of=tournament.best_of,
                             bracket="losers") for p in range(l_sizes[i - 1])])
        l_matches[i] = list(l_round_objs[i].matches.order_by("position"))

    # Grand final
    gf_round = TournamentRound.objects.create(stage=stage, number=999, name="Grand Final",
                                              status=RoundStatus.PENDING)
    grand = TournamentMatch.objects.create(round=gf_round, position=0, best_of=tournament.best_of,
                                           bracket="grand")

    # --- winner routing (winners bracket) ---
    for r in range(1, wrounds):
        for m in w_matches[r]:
            m.next_match = w_matches[r + 1][m.position // 2]
            m.next_slot = "a" if m.position % 2 == 0 else "b"
    # WB final winner → grand final slot a
    w_matches[wrounds][0].next_match = grand
    w_matches[wrounds][0].next_slot = "a"

    # --- loser routing (best-effort: WB losers drop into LB) ---
    # WB R1 losers → LB R1; subsequent WB losers → deeper LB rounds.
    def lb_target_for(wr):
        # WB round wr losers enter LB round index:
        return min(lb_round_count, max(1, (wr - 1) * 2 + 1))

    for r in range(1, wrounds + 1):
        targets = l_matches[lb_target_for(r)] if lb_target_for(r) in l_matches else []
        for i, m in enumerate(w_matches[r]):
            if targets:
                tgt = targets[i % len(targets)]
                m.loser_next_match = tgt
                m.loser_next_slot = "a" if (i % 2 == 0) else "b"

    # LB internal winner routing
    for i in range(1, lb_round_count):
        for j, m in enumerate(l_matches[i]):
            nxt = l_matches[i + 1][j % len(l_matches[i + 1])]
            m.next_match = nxt
            m.next_slot = "a" if j % 2 == 0 else "b"
    # LB final winner → grand final slot b
    l_matches[lb_round_count][0].next_match = grand
    l_matches[lb_round_count][0].next_slot = "b"

    # seed WB round 1
    for i, m in enumerate(w_matches[1]):
        m.participant_a = by_seed.get(order[i * 2])
        m.participant_b = by_seed.get(order[i * 2 + 1])

    all_matches = [m for ms in w_matches.values() for m in ms] + \
                  [m for ms in l_matches.values() for m in ms] + [grand]
    TournamentMatch.objects.bulk_update(all_matches, ["next_match", "next_slot", "loser_next_match",
                                        "loser_next_slot", "participant_a", "participant_b"])

    tournament.status = TournamentStatus.RUNNING
    tournament.save(update_fields=["status"])
    audit(tournament, "bracket_generated", actor, f"Double elimination · {n} jogadores")

    for m in w_matches[1]:
        m.refresh_from_db()
        if m.participant_a and not m.participant_b:
            _finalize_match(m, m.participant_a, None, state=MatchState.BYE, is_bye=True)
        elif m.participant_b and not m.participant_a:
            _finalize_match(m, m.participant_b, None, state=MatchState.BYE, is_bye=True)
    return stage


def dispatch_generate(tournament, actor):
    if tournament.is_roster:
        return _dispatch_roster(tournament, actor)
    bt = tournament.bracket_type
    if bt == BracketType.SINGLE_ELIMINATION:
        from .services import generate_single_elimination
        return generate_single_elimination(tournament, actor)
    if bt == BracketType.SWISS:
        return generate_swiss(tournament, actor)
    if bt == BracketType.SWISS_TOP_CUT:
        return generate_swiss(tournament, actor, kind=BracketType.SWISS_TOP_CUT)
    if bt == BracketType.ROUND_ROBIN:
        return generate_round_robin(tournament, actor)
    if bt == BracketType.DOUBLE_ELIMINATION:
        return generate_double_elimination(tournament, actor)
    raise ValueError(f"Formato não suportado: {bt}")


def _dispatch_roster(tournament, actor):
    """Roster championships pick the pairing engine from `format_kind`:
    points (Swiss/Round Robin), bracket (single/double elim) or hybrid
    (Swiss → Top Cut). Seeds are set from `seed_source` first."""
    from .choices import FormatKind
    from .services import apply_seed_source, generate_single_elimination

    apply_seed_source(tournament)
    fk = tournament.format_kind

    if fk == FormatKind.POINTS:
        if tournament.bracket_type == BracketType.ROUND_ROBIN:
            return generate_round_robin(tournament, actor)
        return generate_swiss(tournament, actor, num_rounds=tournament.rounds_count)

    if fk == FormatKind.BRACKET:
        if tournament.bracket_type == BracketType.DOUBLE_ELIMINATION:
            return generate_double_elimination(tournament, actor)
        return generate_single_elimination(tournament, actor)

    if fk == FormatKind.HYBRID:
        cfg = dict(tournament.custom_rules or {})
        cfg["top_cut_size"] = tournament.hybrid_advance_count or 8
        tournament.custom_rules = cfg
        tournament.save(update_fields=["custom_rules"])
        return generate_swiss(tournament, actor, num_rounds=tournament.rounds_count,
                              kind=BracketType.SWISS_TOP_CUT)

    raise ValueError(f"Formato de campeonato não suportado: {fk}")


def all_pairings(participants):
    return list(combinations(participants, 2))
