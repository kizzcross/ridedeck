import pytest
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
from apps.validation.engine import DeckLine

pytestmark = pytest.mark.django_db


def client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def cards(db):
    s = CardSet.objects.create(code="S", name="Set")
    made = []
    for i in range(4):
        card = Card.objects.create(name=f"Card {i}", grade=i % 4, card_type="normal_unit")
        CardPrinting.objects.create(card_number=f"S-{i:03d}", card_set=s, card=card)
        made.append(card)
    return made


def _version(cards):
    bl = Banlist.objects.create(name="Test", category=BanlistCategory.COMMUNITY,
                                format_code="standard")
    v = BanlistVersion.objects.create(banlist=bl, version=1)
    bl.current_version = v
    bl.save()
    return bl, v


def _lines(pairs):
    """pairs: [(card, qty, zone)] → DeckLine list."""
    return [
        DeckLine(card_uuid=str(c.uuid), name=c.name, zone=z, quantity=q,
                 grade=c.grade, trigger="", nation=c.nation, card_type=c.card_type)
        for c, q, z in pairs
    ]


# --- Acceptance-critical enforcement -------------------------------------
def test_banned_card_invalidates_deck(cards):
    _bl, v = _version(cards)
    BanlistEntry.objects.create(version=v, restriction_type=RestrictionType.BANNED, card=cards[0])
    viols = banlist_violations(_lines([(cards[0], 1, "main_deck")]), v)
    assert any(x["code"] == "BANNED_CARD" for x in viols)


def test_limit_to_1_invalidates_with_two(cards):
    _bl, v = _version(cards)
    BanlistEntry.objects.create(version=v, restriction_type=RestrictionType.LIMIT_TO_1, card=cards[0])
    assert banlist_violations(_lines([(cards[0], 1, "main_deck")]), v) == []
    viols = banlist_violations(_lines([(cards[0], 2, "main_deck")]), v)
    assert any(x["code"] == "LIMIT_EXCEEDED" for x in viols)


def test_choice_restriction_blocks_incompatible(cards):
    _bl, v = _version(cards)
    grp = RestrictionGroup.objects.create(version=v, name="A or B", kind=GroupKind.CHOICE,
                                          limit_value=1)
    RestrictionGroupMember.objects.create(group=grp, card=cards[0])
    RestrictionGroupMember.objects.create(group=grp, card=cards[1])
    BanlistEntry.objects.create(version=v, restriction_type=RestrictionType.CHOICE_RESTRICTION,
                                group=grp)
    # Only A → ok
    assert banlist_violations(_lines([(cards[0], 4, "main_deck")]), v) == []
    # A and B together → violation
    viols = banlist_violations(_lines([(cards[0], 4, "main_deck"), (cards[1], 4, "main_deck")]), v)
    assert any(x["code"] == "CHOICE_RESTRICTION" for x in viols)


def test_max_total_from_group(cards):
    _bl, v = _version(cards)
    grp = RestrictionGroup.objects.create(version=v, name="G", kind=GroupKind.MAX_TOTAL,
                                          limit_value=4)
    RestrictionGroupMember.objects.create(group=grp, card=cards[0])
    RestrictionGroupMember.objects.create(group=grp, card=cards[1])
    BanlistEntry.objects.create(version=v, restriction_type=RestrictionType.MAX_TOTAL_FROM_GROUP,
                                group=grp)
    viols = banlist_violations(_lines([(cards[0], 3, "main_deck"), (cards[1], 3, "main_deck")]), v)
    assert any(x["code"] == "MAX_TOTAL_FROM_GROUP" for x in viols)


# --- Permissions ---------------------------------------------------------
def test_user_creates_community_banlist(member):
    c = client_for(member)
    r = c.post(reverse("v1:banlist-list"),
               {"name": "My list", "format_code": "standard"}, format="json")
    assert r.status_code == 201
    assert r.data["category"] == "community"
    assert r.data["is_official"] is False


def test_user_cannot_make_official(member):
    bl = Banlist.objects.create(name="X", owner=member, category=BanlistCategory.COMMUNITY)
    c = client_for(member)
    r = c.post(reverse("v1:banlist-make-official", args=[bl.uuid]), {}, format="json")
    assert r.status_code == 403
    bl.refresh_from_db()
    assert bl.category == BanlistCategory.COMMUNITY


def test_admin_can_make_official(platform_admin, member):
    bl = Banlist.objects.create(name="X", owner=member, category=BanlistCategory.COMMUNITY)
    c = client_for(platform_admin)
    r = c.post(reverse("v1:banlist-make-official", args=[bl.uuid]), {}, format="json")
    assert r.status_code == 200
    assert r.data["is_official"] is True


def test_fork_creates_community_copy(member, other_member, cards):
    bl, v = _version(cards)
    bl.owner = member
    bl.is_public = True
    bl.save()
    BanlistEntry.objects.create(version=v, restriction_type=RestrictionType.BANNED, card=cards[0])
    c = client_for(other_member)
    r = c.post(reverse("v1:banlist-fork", args=[bl.uuid]))
    assert r.status_code == 201
    forked = Banlist.objects.get(uuid=r.data["uuid"])
    assert forked.owner == other_member
    assert forked.category == "community"
    assert forked.current_version.entries.count() == 1
