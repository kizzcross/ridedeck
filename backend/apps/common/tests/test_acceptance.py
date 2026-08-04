"""The 12 mandated acceptance tests (spec §"Testes específicos"), consolidated as
a single living checklist. Each maps 1:1 to a spec requirement.
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APIClient

from apps.banlists.choices import BanlistCategory, GroupKind, RestrictionType
from apps.banlists.models import (
    Banlist,
    BanlistEntry,
    BanlistVersion,
    RestrictionGroup,
    RestrictionGroupMember,
)
from apps.banlists.services import banlist_violations
from apps.cards.models import Card, CardPrinting, CardSet
from apps.decks.models import Deck
from apps.decks.services import ensure_working_version, set_entry
from apps.powerlevel.models import CardPowerLevel
from apps.tournaments.choices import MatchState, TournamentStatus
from apps.tournaments.models import Tournament, TournamentParticipant
from apps.tournaments.services import (
    confirm_result,
    generate_single_elimination,
    lock_registration,
    register,
    report_result,
    submit_deck,
)
from apps.validation.engine import DeckLine
from apps.validation.service import validate_deck_version

User = get_user_model()
pytestmark = pytest.mark.django_db


def api_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def formats(db):
    call_command("seed_formats")


@pytest.fixture
def cards(db):
    s = CardSet.objects.create(code="S", name="Set")
    made = []
    for i in range(4):
        c = Card.objects.create(name=f"Card {i}", grade=i % 4, card_type="normal_unit",
                                nation="dragon_empire")
        CardPrinting.objects.create(card_number=f"S-{i:03d}", card_set=s, card=c, price="2.00")
        made.append(c)
    return made


# 1
def test_01_member_cannot_edit_power_level(member, cards):
    r = api_for(member).post(reverse("v1:admin-power-set"),
                             {"card": str(cards[0].uuid), "format_code": "standard",
                              "value": 8, "justification": "x"}, format="json")
    assert r.status_code == 403


# 2
def test_02_organizer_cannot_edit_power_level(organizer, cards):
    r = api_for(organizer).post(reverse("v1:admin-power-set"),
                                {"card": str(cards[0].uuid), "format_code": "standard",
                                 "value": 8, "justification": "x"}, format="json")
    assert r.status_code == 403


# 3
def test_03_admin_edits_power_level_with_justification(platform_admin, cards):
    r = api_for(platform_admin).post(reverse("v1:admin-power-set"),
                                     {"card": str(cards[0].uuid), "format_code": "standard",
                                      "value": 8, "justification": "meta call"}, format="json")
    assert r.status_code == 201
    assert CardPowerLevel.objects.get(card=cards[0], format_code="standard").value == 8


# 4
def test_04_missing_owned_copies_does_not_invalidate_deck(member, cards, formats):
    deck = Deck.objects.create(owner=member, title="D", format_code="standard")
    v = ensure_working_version(deck)
    set_entry(v, cards[0], "main_deck", 4)
    result = validate_deck_version(v, owned_map={str(cards[0].uuid): 1})
    assert any(w["code"] == "MISSING_OWNED_COPIES" for w in result["warnings"])
    assert not any("OWNED" in e["code"] for e in result["errors"])


def _lines(pairs):
    return [DeckLine(card_uuid=str(c.uuid), name=c.name, zone=z, quantity=q, grade=c.grade,
                     trigger="", nation=c.nation, card_type=c.card_type) for c, q, z in pairs]


def _banlist_version(cards):
    bl = Banlist.objects.create(name="B", category=BanlistCategory.COMMUNITY, format_code="standard")
    v = BanlistVersion.objects.create(banlist=bl, version=1)
    bl.current_version = v
    bl.save()
    return v


# 5
def test_05_banned_card_invalidates_deck(cards):
    v = _banlist_version(cards)
    BanlistEntry.objects.create(version=v, restriction_type=RestrictionType.BANNED, card=cards[0])
    assert any(x["code"] == "BANNED_CARD"
               for x in banlist_violations(_lines([(cards[0], 1, "main_deck")]), v))


# 6
def test_06_limit_to_1_invalidates_with_two(cards):
    v = _banlist_version(cards)
    BanlistEntry.objects.create(version=v, restriction_type=RestrictionType.LIMIT_TO_1, card=cards[0])
    assert banlist_violations(_lines([(cards[0], 1, "main_deck")]), v) == []
    assert any(x["code"] == "LIMIT_EXCEEDED"
               for x in banlist_violations(_lines([(cards[0], 2, "main_deck")]), v))


# 7
def test_07_choice_restriction_blocks_incompatible(cards):
    v = _banlist_version(cards)
    grp = RestrictionGroup.objects.create(version=v, name="A/B", kind=GroupKind.CHOICE, limit_value=1)
    RestrictionGroupMember.objects.create(group=grp, card=cards[0])
    RestrictionGroupMember.objects.create(group=grp, card=cards[1])
    BanlistEntry.objects.create(version=v, restriction_type=RestrictionType.CHOICE_RESTRICTION, group=grp)
    assert banlist_violations(_lines([(cards[0], 4, "main_deck")]), v) == []
    assert any(x["code"] == "CHOICE_RESTRICTION" for x in banlist_violations(
        _lines([(cards[0], 4, "main_deck"), (cards[1], 4, "main_deck")]), v))


def _four_player_tournament(organizer):
    t = Tournament.objects.create(name="Cup", organizer=organizer, requires_checkin=False,
                                  auto_approve=True, status=TournamentStatus.REGISTRATION)
    players = [User.objects.create_user(email=f"a{i}@t.dev", username=f"a{i}", password="x")
               for i in range(4)]
    for p in players:
        register(t, p)
    return t, players


# 8
def test_08_future_banlist_change_does_not_change_tournament_snapshot(member, formats):
    s = CardSet.objects.create(code="S", name="S")
    card = Card.objects.create(name="Boss", grade=3, card_type="normal_unit")
    CardPrinting.objects.create(card_number="S-1", card_set=s, card=card)
    bl = Banlist.objects.create(name="TB", category=BanlistCategory.COMMUNITY, format_code="standard")
    bv = BanlistVersion.objects.create(banlist=bl, version=1)
    bl.current_version = bv
    bl.save()
    t, players = _four_player_tournament(member)
    t.banlist = bl
    t.save()
    deck = Deck.objects.create(owner=players[0], title="D", format_code="standard")
    v = ensure_working_version(deck)
    set_entry(v, card, "main_deck", 4)
    p = TournamentParticipant.objects.get(tournament=t, user=players[0])
    sub = submit_deck(t, p, deck, players[0])
    before = sub.content_hash
    BanlistEntry.objects.create(version=bv, restriction_type=RestrictionType.BANNED, card=card)
    sub.refresh_from_db()
    assert sub.content_hash == before
    assert not any(e["code"] == "BANNED_CARD" for e in sub.validation["errors"])


# 9
def test_09_editing_original_deck_does_not_change_submission(member):
    s = CardSet.objects.create(code="S", name="S")
    c1 = Card.objects.create(name="A", grade=1, card_type="normal_unit")
    c2 = Card.objects.create(name="B", grade=2, card_type="normal_unit")
    for c in (c1, c2):
        CardPrinting.objects.create(card_number=f"S-{c.name}", card_set=s, card=c)
    t, players = _four_player_tournament(member)
    deck = Deck.objects.create(owner=players[0], title="D", format_code="standard")
    v = ensure_working_version(deck)
    set_entry(v, c1, "main_deck", 4)
    p = TournamentParticipant.objects.get(tournament=t, user=players[0])
    sub = submit_deck(t, p, deck, players[0])
    before = {e["card_uuid"] for e in sub.payload["entries"]}
    set_entry(v, c2, "main_deck", 4)   # edit original afterwards
    sub.refresh_from_db()
    assert {e["card_uuid"] for e in sub.payload["entries"]} == before


# 10
def test_10_bracket_does_not_advance_twice(member):
    t, players = _four_player_tournament(member)
    lock_registration(t, member)
    generate_single_elimination(t, member)
    stage = t.stages.first()
    r1_match = stage.rounds.get(number=1).matches.first()
    final = stage.rounds.get(number=2).matches.first()
    report_result(str(r1_match.uuid), r1_match.participant_a.user, 2, 0)
    confirm_result(str(r1_match.uuid), r1_match.participant_b.user)
    final.refresh_from_db()
    slot = final.participant_a_id
    confirm_result(str(r1_match.uuid), r1_match.participant_b.user)  # duplicate
    final.refresh_from_db()
    assert final.participant_a_id == slot
    r1_match.refresh_from_db()
    assert r1_match.advanced is True and r1_match.state == MatchState.DONE


# 11
def test_11_user_cannot_manage_others_tournament(member, other_member):
    t = Tournament.objects.create(name="X", organizer=member,
                                  status=TournamentStatus.REGISTRATION)
    r = api_for(other_member).post(reverse("v1:tournament-lock", args=[t.uuid]))
    assert r.status_code == 403


# 12
def test_12_community_banlist_not_official_by_member(member):
    bl = Banlist.objects.create(name="X", owner=member, category=BanlistCategory.COMMUNITY)
    r = api_for(member).post(reverse("v1:banlist-make-official", args=[bl.uuid]), {}, format="json")
    assert r.status_code == 403
    bl.refresh_from_db()
    assert bl.category == BanlistCategory.COMMUNITY
