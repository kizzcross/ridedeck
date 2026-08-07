import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.decks.models import Deck
from apps.tournaments.choices import RosterStatus, TournamentKind, TournamentStatus
from apps.tournaments.models import Tournament, TournamentParticipant
from apps.tournaments.roster import (
    add_roster_deck,
    confirm_roster,
    get_or_create_roster,
    set_deck_power,
)
from apps.tournaments.services import lock_registration, register

User = get_user_model()
pytestmark = pytest.mark.django_db


def client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def _roster_tournament(organizer, **kw):
    defaults = dict(
        name="Roster Cup", organizer=organizer, kind=TournamentKind.ROSTER,
        decks_per_player=3, power_cap=10, requires_checkin=False, auto_approve=True,
        status=TournamentStatus.REGISTRATION,
    )
    defaults.update(kw)
    return Tournament.objects.create(**defaults)


def _decks(user, n, fmt="freeplay"):
    # An unseeded format has no rule version, so validate_deck_version passes —
    # letting us exercise roster/cap logic without building 50-card decks.
    return [Deck.objects.create(owner=user, title=f"Deck {i}", format_code=fmt) for i in range(n)]


def _participant(t, user):
    register(t, user)
    return TournamentParticipant.objects.get(tournament=t, user=user)


# --- Roster building ------------------------------------------------------
def test_add_decks_up_to_limit_then_reject(member):
    t = _roster_tournament(member, decks_per_player=3)
    p = _participant(t, member)
    decks = _decks(member, 4)
    for d in decks[:3]:
        add_roster_deck(t, p, d, member)
    roster = get_or_create_roster(t, p)
    assert roster.decks.count() == 3
    with pytest.raises(ValueError):
        add_roster_deck(t, p, decks[3], member)


def test_owner_power_assignment_recomputes_cap(member):
    t = _roster_tournament(member, decks_per_player=3, power_cap=10)
    p = _participant(t, member)
    decks = _decks(member, 3)
    rds = [add_roster_deck(t, p, d, member) for d in decks]
    set_deck_power(rds[0], 4, member)
    set_deck_power(rds[1], 4, member)
    set_deck_power(rds[2], 2, member)
    roster = get_or_create_roster(t, p)
    roster.refresh_from_db()
    assert roster.power_used == 10
    assert roster.is_over_cap is False
    assert roster.status == RosterStatus.VALID
    # Push over the cap → invalid.
    set_deck_power(rds[2], 5, member)
    roster.refresh_from_db()
    assert roster.power_used == 13
    assert roster.is_over_cap is True
    assert roster.status == RosterStatus.INVALID


def test_min_max_power_enforced(member):
    t = _roster_tournament(member, min_deck_power=2, max_deck_power=6)
    p = _participant(t, member)
    rd = add_roster_deck(t, p, _decks(member, 1)[0], member)
    with pytest.raises(ValueError):
        set_deck_power(rd, 7, member)
    with pytest.raises(ValueError):
        set_deck_power(rd, 1, member)


def test_confirm_requires_full_valid_roster(member):
    t = _roster_tournament(member, decks_per_player=3, power_cap=10)
    p = _participant(t, member)
    rds = [add_roster_deck(t, p, d, member) for d in _decks(member, 3)]
    # Powers not set yet → cannot confirm.
    with pytest.raises(ValueError):
        confirm_roster(get_or_create_roster(t, p), member)
    for rd, val in zip(rds, [4, 4, 2], strict=False):
        set_deck_power(rd, val, member)
    roster = confirm_roster(get_or_create_roster(t, p), member)
    assert roster.status == RosterStatus.CONFIRMED


# --- Permissions & endpoints ---------------------------------------------
def test_player_cannot_set_power_via_api(member, other_member):
    t = _roster_tournament(member)
    p = _participant(t, other_member)
    rd = add_roster_deck(t, p, _decks(other_member, 1)[0], other_member)
    r = client_for(other_member).post(
        reverse("v1:tournament-set-deck-power", args=[t.uuid]),
        {"roster_deck": str(rd.uuid), "power": 3}, format="json")
    assert r.status_code == 403


def test_owner_sets_power_via_api(member):
    t = _roster_tournament(member)
    p = _participant(t, member)
    rd = add_roster_deck(t, p, _decks(member, 1)[0], member)
    r = client_for(member).post(
        reverse("v1:tournament-set-deck-power", args=[t.uuid]),
        {"roster_deck": str(rd.uuid), "power": 3}, format="json")
    assert r.status_code == 200
    rd.refresh_from_db()
    assert rd.power == 3


# --- Penalties & visibility ----------------------------------------------
def test_penalty_deducts_points_in_standings(member):
    from apps.tournaments.roster import roster_standings
    from apps.tournaments.services import apply_penalty
    t = _roster_tournament(member)
    p = _participant(t, member)
    apply_penalty(p, "points_deduction", -3, "no-show", member)
    row = next(r for r in roster_standings(t) if r["participant"]["username"] == member.username)
    assert row["penalties"] == -3
    assert row["points"] == -3


def test_closed_roster_hides_decks_from_spectators(member, other_member):
    t = _roster_tournament(member, roster_visibility="closed")
    p = _participant(t, other_member)
    add_roster_deck(t, p, _decks(other_member, 1)[0], member)
    # Organizer sees the decks…
    r_org = client_for(member).get(reverse("v1:tournament-public-rosters", args=[t.uuid]))
    assert r_org.data[0]["decks"]
    # …a third-party spectator does not.
    viewer = User.objects.create_user(email="v@t.dev", username="viewer", password="x")
    r_spec = client_for(viewer).get(reverse("v1:tournament-public-rosters", args=[t.uuid]))
    assert r_spec.data[0].get("decks_hidden") is True
    assert r_spec.data[0]["decks"] == []


# --- Lock freezes rosters -------------------------------------------------
def test_lock_freezes_roster_snapshots(member):
    t = _roster_tournament(member, decks_per_player=2, power_cap=10)
    p = _participant(t, member)
    rds = [add_roster_deck(t, p, d, member) for d in _decks(member, 2)]
    for rd in rds:
        set_deck_power(rd, 3, member)
    lock_registration(t, member)
    roster = get_or_create_roster(t, p)
    roster.refresh_from_db()
    assert roster.status == RosterStatus.LOCKED
    for rd in roster.decks.all():
        assert rd.locked is True
        assert rd.snapshot_id is not None
    # No more edits after lock.
    with pytest.raises(ValueError):
        set_deck_power(roster.decks.first(), 5, member)
