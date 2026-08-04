import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from apps.banlists.choices import BanlistCategory, RestrictionType
from apps.banlists.models import Banlist, BanlistEntry, BanlistVersion
from apps.cards.models import Card, CardPrinting, CardSet
from apps.decks.models import Deck
from apps.decks.services import ensure_working_version, set_entry
from apps.tournaments.choices import MatchState, TournamentStatus
from apps.tournaments.models import Tournament, TournamentMatch
from apps.tournaments.services import (
    confirm_result,
    generate_single_elimination,
    lock_registration,
    register,
    report_result,
)

User = get_user_model()
pytestmark = pytest.mark.django_db


def client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def formats(db):
    call_command("seed_formats")


@pytest.fixture
def players(db):
    return [User.objects.create_user(email=f"p{i}@t.dev", username=f"p{i}", password="x")
            for i in range(4)]


def _tournament(organizer, **kw):
    defaults = dict(name="Cup", organizer=organizer, requires_checkin=False,
                    auto_approve=True, status=TournamentStatus.REGISTRATION)
    defaults.update(kw)
    return Tournament.objects.create(**defaults)


# --- Permissions ----------------------------------------------------------
def test_any_user_creates_tournament_and_becomes_organizer(member):
    c = client_for(member)
    r = c.post(reverse("v1:tournament-list"), {"name": "My Cup"}, format="json")
    assert r.status_code == 201
    assert r.data["is_organizer"] is True
    assert Tournament.objects.get(name="My Cup").organizer == member


def test_non_organizer_cannot_manage(member, other_member):
    t = _tournament(member)
    r = client_for(other_member).post(reverse("v1:tournament-lock", args=[t.uuid]))
    assert r.status_code == 403


def test_organizer_lifecycle_and_bracket(member, players):
    t = _tournament(member)
    for p in players:
        register(t, p)
    lock_registration(t, member)
    stage = generate_single_elimination(t, member)
    assert stage.rounds.count() == 2                 # 4 players → 2 rounds
    assert TournamentMatch.objects.filter(round__stage=stage).count() == 3  # 2 + 1
    t.refresh_from_db()
    assert t.status == TournamentStatus.RUNNING


# --- Idempotent advance ---------------------------------------------------
def test_bracket_does_not_advance_twice(member, players):
    t = _tournament(member)
    for p in players:
        register(t, p)
    lock_registration(t, member)
    generate_single_elimination(t, member)
    r1 = t.stages.first().rounds.get(number=1)
    final = t.stages.first().rounds.get(number=2).matches.first()

    m = r1.matches.first()
    report_result(str(m.uuid), m.participant_a.user, 2, 0)
    confirm_result(str(m.uuid), m.participant_b.user)
    final.refresh_from_db()
    winner_after_first = final.participant_a_id

    # duplicate confirm — must NOT change anything / advance twice
    confirm_result(str(m.uuid), m.participant_b.user)
    confirm_result(str(m.uuid), m.participant_b.user)
    final.refresh_from_db()
    assert final.participant_a_id == winner_after_first
    m.refresh_from_db()
    assert m.state == MatchState.DONE and m.advanced is True


def test_full_run_produces_champion(member, players):
    t = _tournament(member)
    for p in players:
        register(t, p)
    lock_registration(t, member)
    generate_single_elimination(t, member)
    stage = t.stages.first()
    for rnd in stage.rounds.order_by("number"):
        for m in rnd.matches.all():
            m.refresh_from_db()
            if m.state in (MatchState.DONE, MatchState.BYE):
                continue
            report_result(str(m.uuid), m.participant_a.user, 2, 1)
            confirm_result(str(m.uuid), m.participant_b.user)
    t.refresh_from_db()
    assert t.status == TournamentStatus.FINISHED
    assert t.standings.filter(rank=1).exists()


# --- Snapshot immutability ------------------------------------------------
def test_submitted_deck_frozen_against_later_banlist_change(member, players, formats):
    s = CardSet.objects.create(code="S", name="S")
    card = Card.objects.create(name="Boss", grade=3, card_type="normal_unit", nation="dragon_empire")
    CardPrinting.objects.create(card_number="S-1", card_set=s, card=card)

    bl = Banlist.objects.create(name="TB", category=BanlistCategory.COMMUNITY, format_code="standard")
    bv = BanlistVersion.objects.create(banlist=bl, version=1)
    bl.current_version = bv
    bl.save()

    t = _tournament(member, banlist=bl)
    p = players[0]
    register(t, p)
    deck = Deck.objects.create(owner=p, title="D", format_code="standard")
    version = ensure_working_version(deck)
    set_entry(version, card, "main_deck", 4)

    from apps.tournaments.models import TournamentParticipant
    from apps.tournaments.services import submit_deck
    participant = TournamentParticipant.objects.get(tournament=t, user=p)
    sub = submit_deck(t, participant, deck, p)
    hash_before = sub.content_hash
    # Not banned at submission time → no BANNED_CARD in the frozen validation.
    assert not any(e["code"] == "BANNED_CARD" for e in sub.validation["errors"])

    # Later: ban the card globally on the banlist.
    BanlistEntry.objects.create(version=bv, restriction_type=RestrictionType.BANNED, card=card)
    # The stored submission is unchanged — snapshot immutability.
    sub.refresh_from_db()
    assert sub.content_hash == hash_before
    assert not any(e["code"] == "BANNED_CARD" for e in sub.validation["errors"])


def test_submitting_then_editing_deck_does_not_change_submission(member, players, formats):
    s = CardSet.objects.create(code="S", name="S")
    c1 = Card.objects.create(name="A", grade=1, card_type="normal_unit")
    c2 = Card.objects.create(name="B", grade=2, card_type="normal_unit")
    CardPrinting.objects.create(card_number="S-1", card_set=s, card=c1)
    CardPrinting.objects.create(card_number="S-2", card_set=s, card=c2)

    t = _tournament(member)
    p = players[0]
    register(t, p)
    deck = Deck.objects.create(owner=p, title="D", format_code="standard")
    v = ensure_working_version(deck)
    set_entry(v, c1, "main_deck", 4)

    from apps.tournaments.models import TournamentParticipant
    from apps.tournaments.services import submit_deck
    participant = TournamentParticipant.objects.get(tournament=t, user=p)
    sub = submit_deck(t, participant, deck, p)
    before = [e["card_uuid"] for e in sub.payload["entries"]]

    # Edit the source deck afterwards.
    set_entry(v, c2, "main_deck", 4)
    sub.refresh_from_db()
    after = [e["card_uuid"] for e in sub.payload["entries"]]
    assert before == after and str(c2.uuid) not in after
