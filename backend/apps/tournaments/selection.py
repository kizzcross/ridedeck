"""Per-round deck selection & draw engine for roster championships.

Each Vanguard match is 1 deck per player; this module decides WHICH deck from a
participant's (locked) roster is used in a given match, per the tournament's
`deck_selection_mode`. Draws are server-side and persisted (never recomputed on
the client) and every draw writes an immutable `DeckDrawLog`. A participant's
pick stays secret until BOTH sides confirm — the reveal is gated here.
"""
from __future__ import annotations

import secrets

from django.db import transaction

from .choices import (
    DeckSelectionMode,
    MatchState,
    SelectionMethod,
)
from .models import (
    DeckDrawLog,
    MatchDeckSelection,
    RosterDeck,
    RosterDeckSequence,
    TournamentRoster,
)
from .services import audit


def roster_of(tournament, participant) -> TournamentRoster | None:
    return TournamentRoster.objects.filter(tournament=tournament, participant=participant).first()


def _prior_picks(tournament, participant, before_round: int) -> list[int]:
    """Ordered roster_deck ids the participant already used in earlier rounds."""
    qs = (MatchDeckSelection.objects
          .filter(participant=participant, match__round__stage__tournament=tournament,
                  roster_deck__isnull=False, match__round__number__lt=before_round)
          .order_by("match__round__number")
          .values_list("roster_deck_id", flat=True))
    return list(qs)


def eligible_decks(tournament, roster, round_number: int) -> list[RosterDeck]:
    """The roster decks a participant may draw/use this round, per the mode's
    repetition rule. (Ace-specific weighting/extra handled in `_pick`.)"""
    decks = list(roster.decks.all())
    mode = tournament.deck_selection_mode
    prior = _prior_picks(tournament, roster.participant, round_number)

    if mode == DeckSelectionMode.RANDOM_NO_CONSECUTIVE and prior:
        last = prior[-1]
        pool = [d for d in decks if d.id != last]
        return pool or decks

    if mode == DeckSelectionMode.RANDOM_ROTATION:
        from collections import Counter
        cycle = tournament.decks_per_player or len(decks) or 1
        rem = len(prior) % cycle
        window = prior[len(prior) - rem:] if rem else []
        counts = Counter(window)
        # The Ace may appear one extra time per cycle under the extra-in-rotation rule.
        extra_ace = tournament.ace_enabled and tournament.ace_rule == "extra_in_rotation"
        ace_id = next((d.id for d in decks if d.is_ace), None)

        def allowed(d):
            cap = 2 if (extra_ace and d.id == ace_id) else 1
            return counts.get(d.id, 0) < cap

        pool = [d for d in decks if allowed(d)]
        return pool or decks

    return decks


def _pick(tournament, roster, pool: list[RosterDeck]) -> RosterDeck:
    """Random selection over `pool`, honouring the weighted-random Ace rule."""
    if not pool:
        pool = list(roster.decks.all())
    if tournament.ace_enabled and tournament.ace_rule == "weighted_random":
        weighted: list[RosterDeck] = []
        for d in pool:
            weighted.extend([d, d] if d.is_ace else [d])
        pool = weighted or pool
    return secrets.choice(pool)


@transaction.atomic
def _log_draw(tournament, round_obj, participant, result_deck, eligible, rule,
              options=None, admin_intervention=False, admin=None):
    DeckDrawLog.objects.create(
        tournament=tournament, round=round_obj, participant=participant,
        result_deck=result_deck, eligible=[str(d.uuid) for d in eligible],
        options=options or [], rule=rule, admin_intervention=admin_intervention, admin=admin,
    )


def _sequence_deck(tournament, roster, round_number: int) -> RosterDeck | None:
    """Predetermined mode: the frozen deck for this round (cycles the stored
    first-cycle permutation)."""
    rows = list(roster.sequence.order_by("round_number"))
    if not rows:
        return None
    idx = (round_number - 1) % len(rows)
    return rows[idx].roster_deck


@transaction.atomic
def ensure_selection(match, participant, actor, *, admin_intervention=False):
    """Create/populate the MatchDeckSelection for (match, participant) according
    to the tournament mode. Idempotent unless `admin_intervention` forces a redraw.
    Returns the selection (or None for a bye side)."""
    if participant is None:
        return None
    tournament = match.round.stage.tournament
    roster = roster_of(tournament, participant)
    if not roster:
        return None
    round_obj = match.round
    mode = tournament.deck_selection_mode

    sel, created = MatchDeckSelection.objects.get_or_create(match=match, participant=participant)
    if sel.confirmed and not admin_intervention:
        return sel
    # Set the selection up exactly once. Idempotent re-runs (drawing happens after
    # every match finalise) must NOT wipe an existing draw or an in-progress manual
    # pick — only an explicit admin redraw re-rolls it.
    if not created and not admin_intervention:
        return sel

    pool = eligible_decks(tournament, roster, round_obj.number)

    if mode == DeckSelectionMode.MANUAL:
        sel.method = SelectionMethod.MANUAL
        sel.rule_used = mode
        sel.eligible = [str(d.uuid) for d in roster.decks.all()]
        sel.roster_deck = None
        sel.confirmed = False
        sel.save()
        return sel

    if mode == DeckSelectionMode.CHOOSE_FROM_RANDOM:
        n = min(tournament.random_options_count or 2, len(pool)) or 1
        options = []
        available = list(pool)
        for _ in range(n):
            if not available:
                break
            d = secrets.choice(available)
            available.remove(d)
            options.append(d)
        sel.method = SelectionMethod.CHOOSE_FROM_RANDOM
        sel.rule_used = mode
        sel.options = [str(d.uuid) for d in options]
        sel.eligible = [str(d.uuid) for d in pool]
        sel.roster_deck = None
        sel.confirmed = False
        sel.save()
        _log_draw(tournament, round_obj, participant, None, options, rule=f"{mode}:options",
                  options=[str(d.uuid) for d in options], admin_intervention=admin_intervention,
                  admin=actor if admin_intervention else None)
        return sel

    if mode == DeckSelectionMode.PREDETERMINED_ORDER:
        deck = _sequence_deck(tournament, roster, round_obj.number)
        sel.method = SelectionMethod.PREDETERMINED
        sel.rule_used = mode
        sel.roster_deck = deck
        sel.eligible = [str(d.uuid) for d in roster.decks.all()]
        sel.is_ace_used = bool(deck and deck.is_ace)
        sel.save()
        _log_draw(tournament, round_obj, participant, deck, roster.decks.all(), rule=mode,
                  admin_intervention=admin_intervention, admin=actor if admin_intervention else None)
        return sel

    # Random family (free / no_consecutive / rotation)
    deck = _pick(tournament, roster, pool)
    sel.method = SelectionMethod.RANDOM
    sel.rule_used = mode
    sel.roster_deck = deck
    sel.eligible = [str(d.uuid) for d in pool]
    sel.is_ace_used = bool(deck and deck.is_ace)
    sel.save()
    _log_draw(tournament, round_obj, participant, deck, pool, rule=mode,
              admin_intervention=admin_intervention, admin=actor if admin_intervention else None)
    return sel


@transaction.atomic
def run_round_draws(round_obj, actor, *, admin_intervention=False):
    """Ensure selections for every active match in the round."""
    tournament = round_obj.stage.tournament
    for match in round_obj.matches.all():
        if match.state in (MatchState.DONE, MatchState.BYE):
            continue
        ensure_selection(match, match.participant_a, actor, admin_intervention=admin_intervention)
        ensure_selection(match, match.participant_b, actor, admin_intervention=admin_intervention)
    audit(tournament, "round_draws", actor,
          f"Sorteios da rodada {round_obj.number}"
          + (" (intervenção do organizador)" if admin_intervention else ""))


def run_active_round_draws(tournament, actor, *, admin_intervention=False):
    """Run draws for every active round (used after pairing / at round start)."""
    from .choices import RoundStatus
    for stage in tournament.stages.all():
        for rnd in stage.rounds.filter(status=RoundStatus.ACTIVE):
            run_round_draws(rnd, actor, admin_intervention=admin_intervention)


@transaction.atomic
def player_pick(match, participant, roster_deck_uuid) -> MatchDeckSelection:
    """Manual / choose-from-random: the player selects a deck (secret until both
    confirm)."""
    tournament = match.round.stage.tournament
    roster = roster_of(tournament, participant)
    sel = MatchDeckSelection.objects.select_for_update().get(match=match, participant=participant)
    if sel.confirmed:
        raise ValueError("Escolha já confirmada.")
    rd = roster.decks.filter(uuid=roster_deck_uuid).first() if roster else None
    if not rd:
        raise ValueError("Deck não pertence ao seu roster.")
    if sel.method == SelectionMethod.CHOOSE_FROM_RANDOM and str(rd.uuid) not in (sel.options or []):
        raise ValueError("Escolha um dos decks sorteados.")
    sel.roster_deck = rd
    sel.is_ace_used = rd.is_ace
    sel.save(update_fields=["roster_deck", "is_ace_used"])
    return sel


@transaction.atomic
def confirm_selection(match, participant) -> MatchDeckSelection:
    """Player confirms they're ready. When BOTH sides are confirmed, reveal."""
    sel = MatchDeckSelection.objects.select_for_update().get(match=match, participant=participant)
    if sel.roster_deck_id is None:
        raise ValueError("Escolha um deck antes de confirmar.")
    sel.confirmed = True
    sel.save(update_fields=["confirmed"])
    _maybe_reveal(match)
    return sel


@transaction.atomic
def use_ace(match, participant) -> MatchDeckSelection:
    """The player spends their Ace for this match (manual_once / replace_draw
    rules): the Ace deck becomes the deck for this round. Allowed once per event."""
    from .models import AceEvent
    tournament = match.round.stage.tournament
    if not (tournament.ace_enabled and tournament.ace_rule in ("manual_once", "replace_draw")):
        raise ValueError("O Ace não pode ser usado neste campeonato.")
    roster = roster_of(tournament, participant)
    ace = roster.decks.filter(is_ace=True).first() if roster else None
    if not ace:
        raise ValueError("Você não escolheu um Ace.")
    already = AceEvent.objects.filter(roster=roster, kind__in=("used", "replaced_draw")).exists()
    if already:
        raise ValueError("Você já usou o seu Ace neste campeonato.")
    sel = MatchDeckSelection.objects.select_for_update().get(match=match, participant=participant)
    if sel.confirmed:
        raise ValueError("A escolha já foi confirmada.")
    sel.roster_deck = ace
    sel.is_ace_used = True
    sel.rule_used = f"{sel.rule_used}+ace"
    sel.save(update_fields=["roster_deck", "is_ace_used", "rule_used"])
    kind = "replaced_draw" if tournament.ace_rule == "replace_draw" else "used"
    AceEvent.objects.create(roster=roster, match=match, kind=kind)
    audit(tournament, "ace_used", participant.user,
          f"{participant.user.username} usou o Ace ({ace.label})")
    return sel


def _maybe_reveal(match):
    """Reveal both selections once every present side has confirmed."""
    sides = [p for p in (match.participant_a_id, match.participant_b_id) if p]
    sels = list(MatchDeckSelection.objects.select_for_update().filter(match=match))
    present = [s for s in sels if s.participant_id in sides]
    if len(present) == len(sides) and all(s.confirmed for s in present):
        for s in present:
            if not s.revealed:
                s.revealed = True
                s.save(update_fields=["revealed"])
        if match.state == MatchState.PENDING:
            match.state = MatchState.PENDING  # play state kept; report flow unchanged
        # Log Ace reveals for hidden-until-first-use rule.
        tournament = match.round.stage.tournament
        if tournament.ace_enabled:
            from .models import AceEvent
            for s in present:
                if s.is_ace_used and s.roster_deck_id:
                    AceEvent.objects.get_or_create(
                        roster=s.roster_deck.roster, match=match, kind="revealed")


def build_predetermined_sequences(tournament, actor=None):
    """At lock: for predetermined mode, freeze a shuffled first-cycle order per
    roster. Later rounds cycle this permutation."""
    if tournament.deck_selection_mode != DeckSelectionMode.PREDETERMINED_ORDER:
        return
    for roster in tournament.rosters.prefetch_related("decks"):
        if roster.sequence.exists():
            continue
        decks = list(roster.decks.all())
        # Shuffle without Math.random constraints (server-side, persisted).
        order = decks[:]
        for i in range(len(order) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            order[i], order[j] = order[j], order[i]
        RosterDeckSequence.objects.bulk_create([
            RosterDeckSequence(roster=roster, round_number=i + 1, roster_deck=d)
            for i, d in enumerate(order)
        ])
    audit(tournament, "sequences_built", actor, "Sequências pré-definidas congeladas")
