import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.decks.models import Deck
from apps.tournaments.choices import (
    BracketType,
    DeckSelectionMode,
    RoundStatus,
    TournamentKind,
    TournamentStatus,
)
from apps.tournaments.models import (
    DeckDrawLog,
    MatchDeckSelection,
    Tournament,
    TournamentMatch,
    TournamentParticipant,
    TournamentRound,
    TournamentStage,
)
from apps.tournaments.roster import add_roster_deck, lock_rosters, set_deck_power
from apps.tournaments.selection import confirm_selection, ensure_selection, player_pick
from apps.tournaments.services import register

User = get_user_model()
pytestmark = pytest.mark.django_db


def _setup(organizer, mode, *, decks_per_player=3, cap=30):
    t = Tournament.objects.create(
        name="Sel Cup", organizer=organizer, kind=TournamentKind.ROSTER,
        decks_per_player=decks_per_player, power_cap=cap, deck_selection_mode=mode,
        requires_checkin=False, auto_approve=True, status=TournamentStatus.REGISTRATION,
    )
    players = [User.objects.create_user(email=f"s{i}@t.dev", username=f"s{i}", password="x")
               for i in range(2)]
    parts = []
    for u in players:
        register(t, u)
        p = TournamentParticipant.objects.get(tournament=t, user=u)
        for i in range(decks_per_player):
            d = Deck.objects.create(owner=u, title=f"{u.username}-D{i}", format_code="freeplay")
            rd = add_roster_deck(t, p, d, u)
            set_deck_power(rd, 2, organizer)
        parts.append(p)
    lock_rosters(t, organizer)
    stage = TournamentStage.objects.create(tournament=t, kind=BracketType.ROUND_ROBIN, name="S")
    return t, parts, stage


def _round_match(stage, number, pa, pb):
    rnd = TournamentRound.objects.create(stage=stage, number=number, status=RoundStatus.ACTIVE)
    return TournamentMatch.objects.create(round=rnd, position=0, participant_a=pa, participant_b=pb)


def test_roster_bracket_generation_autodraws_decks(member):
    from django.urls import reverse

    from apps.tournaments.choices import FormatKind
    from apps.tournaments.services import lock_registration
    U = get_user_model()
    t = Tournament.objects.create(
        name="Gen Cup", organizer=member, kind=TournamentKind.ROSTER, format_code="freeplay",
        decks_per_player=2, power_cap=10, deck_selection_mode=DeckSelectionMode.RANDOM_FREE,
        format_kind=FormatKind.BRACKET, bracket_type=BracketType.SINGLE_ELIMINATION,
        requires_checkin=False, auto_approve=True, status=TournamentStatus.REGISTRATION)
    for i in range(2):
        u = U.objects.create_user(email=f"g{i}@t.dev", username=f"g{i}", password="x")
        register(t, u)
        p = TournamentParticipant.objects.get(tournament=t, user=u)
        for j in range(2):
            d = Deck.objects.create(owner=u, title=f"{u.username}-{j}", format_code="freeplay")
            set_deck_power(add_roster_deck(t, p, d, member), 3, member)
    lock_registration(t, member)
    r = APIClient()
    r.force_authenticate(user=member)
    resp = r.post(reverse("v1:tournament-generate-bracket", args=[t.uuid]))
    assert resp.status_code == 201
    # Both participants in the first match had a deck drawn automatically.
    assert MatchDeckSelection.objects.filter(match__round__stage__tournament=t).count() == 2


def _draw_sequence(t, stage, part, opp, rounds):
    picks = []
    for r in range(1, rounds + 1):
        m = _round_match(stage, r, part, opp)
        sel = ensure_selection(m, part, t.organizer)
        picks.append(sel.roster_deck_id)
    return picks


# --- Rotation: no repeat until the whole cycle is used --------------------
def test_rotation_uses_all_before_repeat(member):
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.RANDOM_ROTATION, decks_per_player=3)
    picks = _draw_sequence(t, stage, pa, pb, 3)
    assert len(set(picks)) == 3            # all three distinct within the cycle
    # Round 4 starts a new cycle → any deck is eligible again.
    m4 = _round_match(stage, 4, pa, pb)
    sel4 = ensure_selection(m4, pa, member)
    assert sel4.roster_deck_id in picks    # a repeat is now allowed


def test_no_consecutive_never_repeats_back_to_back(member):
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.RANDOM_NO_CONSECUTIVE, decks_per_player=2)
    picks = _draw_sequence(t, stage, pa, pb, 5)
    for a, b in zip(picks, picks[1:], strict=False):
        assert a != b


def test_random_draw_writes_immutable_log(member):
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.RANDOM_FREE, decks_per_player=3)
    m = _round_match(stage, 1, pa, pb)
    sel = ensure_selection(m, pa, member)
    log = DeckDrawLog.objects.filter(tournament=t, participant=pa).first()
    assert log is not None
    assert log.result_deck_id == sel.roster_deck_id
    assert len(log.eligible) == 3
    assert log.admin_intervention is False


# --- Predetermined: frozen sequence, cycles per cap -----------------------
def test_predetermined_sequence_is_frozen_and_cycles(member):
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.PREDETERMINED_ORDER, decks_per_player=3)
    picks = _draw_sequence(t, stage, pa, pb, 3)
    assert len(set(picks)) == 3
    m4 = _round_match(stage, 4, pa, pb)
    sel4 = ensure_selection(m4, pa, member)
    assert sel4.roster_deck_id == picks[0]   # round 4 == round 1 (cycle length 3)


# --- Manual: secret until BOTH confirm ------------------------------------
def test_manual_pick_hidden_until_both_confirm(member):
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.MANUAL, decks_per_player=3)
    m = _round_match(stage, 1, pa, pb)
    ensure_selection(m, pa, member)
    ensure_selection(m, pb, member)
    da = pa.roster.decks.first()
    db = pb.roster.decks.first()
    player_pick(m, pa, da.uuid)
    confirm_selection(m, pa)
    # Only one side confirmed → nothing revealed yet.
    assert not MatchDeckSelection.objects.get(match=m, participant=pa).revealed
    player_pick(m, pb, db.uuid)
    confirm_selection(m, pb)
    # Both confirmed → both revealed.
    assert MatchDeckSelection.objects.get(match=m, participant=pa).revealed
    assert MatchDeckSelection.objects.get(match=m, participant=pb).revealed


def test_manual_pick_survives_idempotent_redraw(member):
    # Regression: re-running draws (which happens after every match finalises)
    # must not wipe an unconfirmed manual pick.
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.MANUAL, decks_per_player=3)
    m = _round_match(stage, 1, pa, pb)
    ensure_selection(m, pa, member)
    da = pa.roster.decks.first()
    player_pick(m, pa, da.uuid)
    ensure_selection(m, pa, member)  # non-admin re-run
    assert MatchDeckSelection.objects.get(match=m, participant=pa).roster_deck_id == da.id


def test_random_draw_is_stable_across_reruns(member):
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.RANDOM_FREE, decks_per_player=3)
    m = _round_match(stage, 1, pa, pb)
    first = ensure_selection(m, pa, member).roster_deck_id
    again = ensure_selection(m, pa, member).roster_deck_id
    assert first == again  # not re-rolled


def _sel_for(payload, participant):
    for rnd in payload:
        for m in rnd["matches"]:
            for s in m["selections"]:
                if s["participant_uuid"] == str(participant.uuid):
                    return s
    return None


def test_opponent_deck_hidden_until_both_confirm_via_api(member):
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.MANUAL, decks_per_player=3)
    m = _round_match(stage, 1, pa, pb)
    ensure_selection(m, pa, member)
    ensure_selection(m, pb, member)
    da = pa.roster.decks.first()
    player_pick(m, pa, da.uuid)
    confirm_selection(m, pa)  # pa ready; pb not yet

    ca = APIClient()
    ca.force_authenticate(user=pb.user)  # pb views the round
    payload = ca.get(reverse("v1:tournament-roster-rounds", args=[t.uuid])).data
    # pb must NOT see pa's deck yet (pa confirmed but pb hasn't → not revealed).
    assert _sel_for(payload, pa)["deck"] is None

    db = pb.roster.decks.first()
    player_pick(m, pb, db.uuid)
    confirm_selection(m, pb)
    payload2 = ca.get(reverse("v1:tournament-roster-rounds", args=[t.uuid])).data
    assert _sel_for(payload2, pa)["deck"] is not None      # now revealed
    assert _sel_for(payload2, pb)["deck"] is not None


def test_use_ace_once_only(member):
    from apps.tournaments.choices import AceRule
    from apps.tournaments.selection import use_ace
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.RANDOM_FREE, decks_per_player=3)
    t.ace_enabled = True
    t.ace_rule = AceRule.REPLACE_DRAW
    t.save()
    ace = pa.roster.decks.first()
    ace.is_ace = True
    ace.save()
    m1 = _round_match(stage, 1, pa, pb)
    ensure_selection(m1, pa, member)
    sel = use_ace(m1, pa)
    assert sel.roster_deck_id == ace.id and sel.is_ace_used
    # A second use anywhere is rejected.
    m2 = _round_match(stage, 2, pa, pb)
    ensure_selection(m2, pa, member)
    with pytest.raises(ValueError):
        use_ace(m2, pa)


def test_dispute_resolution_sets_winner(member):
    from apps.tournaments.choices import MatchState
    from apps.tournaments.models import MatchDispute
    from apps.tournaments.services import resolve_dispute
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.RANDOM_FREE, decks_per_player=2)
    m = _round_match(stage, 1, pa, pb)
    MatchDispute.objects.create(match=m, opened_by=pa.user, reason="placar errado")
    m.state = MatchState.DISPUTED
    m.save(update_fields=["state"])
    resolve_dispute(m, member, "corrigido", 1, 0)
    m.refresh_from_db()
    assert m.state == MatchState.DONE
    assert m.winner_id == pa.id
    assert not MatchDispute.objects.filter(match=m, resolved=False).exists()


def test_roster_standings_counts_ace_wins(member):
    from apps.tournaments.choices import AceRule, MatchState
    from apps.tournaments.roster import roster_standings
    from apps.tournaments.services import _finalize_match
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.RANDOM_FREE, decks_per_player=3)
    t.ace_enabled = True
    t.ace_rule = AceRule.TIEBREAK_WINS
    t.save()
    ace = pa.roster.decks.first()
    ace.is_ace = True
    ace.save()
    m = _round_match(stage, 1, pa, pb)
    sel = ensure_selection(m, pa, member)
    sel.roster_deck = ace
    sel.is_ace_used = True
    sel.save()
    ensure_selection(m, pb, member)
    m.score_a, m.score_b = 1, 0
    m.save(update_fields=["score_a", "score_b"])
    _finalize_match(m, pa, member, state=MatchState.DONE)
    rows = roster_standings(t)
    top = next(r for r in rows if r["participant"]["username"] == pa.user.username)
    assert top["ace_wins"] == 1


def test_choose_from_random_offers_options_and_validates_pick(member):
    t, (pa, pb), stage = _setup(member, DeckSelectionMode.CHOOSE_FROM_RANDOM, decks_per_player=3)
    m = _round_match(stage, 1, pa, pb)
    sel = ensure_selection(m, pa, member)
    assert len(sel.options) == t.random_options_count == 2
    # Picking a deck outside the offered options is rejected.
    outside = pa.roster.decks.exclude(uuid__in=sel.options).first()
    if outside:
        with pytest.raises(ValueError):
            player_pick(m, pa, outside.uuid)
    # Picking an offered deck works.
    player_pick(m, pa, sel.options[0])
    assert str(MatchDeckSelection.objects.get(match=m, participant=pa).roster_deck.uuid) == sel.options[0]
