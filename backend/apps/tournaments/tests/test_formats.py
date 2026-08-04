import pytest
from django.contrib.auth import get_user_model

from apps.tournaments.choices import BracketType, MatchState, TournamentStatus
from apps.tournaments.formats import (
    generate_double_elimination,
    generate_round_robin,
    generate_swiss,
)
from apps.tournaments.models import Tournament, TournamentMatch
from apps.tournaments.services import (
    compute_swiss_standings,
    confirm_result,
    lock_registration,
    register,
    report_result,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


def _players(n):
    return [User.objects.create_user(email=f"f{i}@t.dev", username=f"f{i}", password="x")
            for i in range(n)]


def _tournament(org, **kw):
    d = dict(name="F", organizer=org, requires_checkin=False, auto_approve=True,
             status=TournamentStatus.REGISTRATION)
    d.update(kw)
    t = Tournament.objects.create(**d)
    return t


def _play_round(round_obj, draw=False):
    for m in round_obj.matches.all():
        m.refresh_from_db()
        if m.state in (MatchState.DONE, MatchState.BYE) or not (m.participant_a_id and m.participant_b_id):
            continue
        report_result(str(m.uuid), m.participant_a.user, 1 if draw else 2, 1)
        confirm_result(str(m.uuid), m.participant_b.user)


def test_round_robin_all_play_each_other(member):
    players = _players(4)
    t = _tournament(member)
    for p in players:
        register(t, p)
    lock_registration(t, member)
    stage = generate_round_robin(t, member)
    assert stage.rounds.count() == 3            # 4 players → 3 rounds
    # each player faces 3 distinct opponents
    faced = {p.id: set() for p in t.participants.all()}
    for m in TournamentMatch.objects.filter(round__stage=stage):
        if m.participant_a_id and m.participant_b_id:
            faced[m.participant_a_id].add(m.participant_b_id)
            faced[m.participant_b_id].add(m.participant_a_id)
    assert all(len(v) == 3 for v in faced.values())


def test_swiss_generates_rounds_and_standings_with_tiebreaks(member):
    players = _players(4)
    t = _tournament(member)
    for p in players:
        register(t, p)
    lock_registration(t, member)
    stage = generate_swiss(t, member, num_rounds=3)
    assert stage.kind == BracketType.SWISS
    # play all 3 rounds
    for _ in range(3):
        active = stage.rounds.filter(status="active").first()
        if not active:
            break
        _play_round(active)
    standings = compute_swiss_standings(t)
    assert len(standings) == 4
    assert "omw" in standings[0]["tiebreaks"]
    # points are non-increasing down the standings
    pts = [s["points"] for s in standings]
    assert pts == sorted(pts, reverse=True)
    t.refresh_from_db()
    assert t.status == TournamentStatus.FINISHED


def test_swiss_allows_draws(member):
    players = _players(2)
    t = _tournament(member)
    for p in players:
        register(t, p)
    lock_registration(t, member)
    stage = generate_swiss(t, member, num_rounds=1)
    m = stage.rounds.first().matches.first()
    report_result(str(m.uuid), m.participant_a.user, 1, 1)
    confirm_result(str(m.uuid), m.participant_b.user)   # draw allowed in Swiss
    m.refresh_from_db()
    assert m.is_draw is True
    standings = compute_swiss_standings(t)
    assert all(s["points"] == 1 for s in standings)     # both got a draw point


def test_double_elimination_has_winners_and_losers(member):
    players = _players(4)
    t = _tournament(member)
    for p in players:
        register(t, p)
    lock_registration(t, member)
    stage = generate_double_elimination(t, member)
    brackets = set(TournamentMatch.objects.filter(round__stage=stage)
                   .values_list("bracket", flat=True))
    assert "winners" in brackets and "losers" in brackets and "grand" in brackets
    # a WB round-1 match routes its loser somewhere
    wb1 = TournamentMatch.objects.filter(round__stage=stage, bracket="winners",
                                         round__number=1).first()
    assert wb1.loser_next_match_id is not None
