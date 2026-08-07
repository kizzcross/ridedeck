import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.cards.models import Card, CardSet
from apps.decks.models import Deck, DeckEntry

pytestmark = pytest.mark.django_db


def client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def cards(db):
    s = CardSet.objects.create(code="S", name="Set")
    made = []
    for i in range(6):
        c = Card.objects.create(
            name=f"Card {i}", grade=i % 4, card_type="normal_unit",
            trigger="critical" if i == 0 else "",
        )
        c.printings.create(card_number=f"S-{i:03d}", card_set=s)
        made.append(c)
    return made


@pytest.fixture
def deck(member, cards):
    c = client_for(member)
    resp = c.post(reverse("v1:deck-list"), {"title": "My Deck", "format_code": "standard"},
                  format="json")
    assert resp.status_code == 201
    return Deck.objects.get(title="My Deck")


def test_create_deck_makes_working_version(deck):
    assert deck.current_version is not None
    assert deck.visibility == "private"


def test_create_response_includes_uuid_and_version(member):
    c = client_for(member)
    resp = c.post(reverse("v1:deck-list"), {"title": "X", "format_code": "standard"}, format="json")
    assert resp.status_code == 201
    assert "uuid" in resp.data and resp.data["uuid"]
    assert resp.data["current_version"] is not None


def test_add_and_remove_entry(member, deck, cards):
    c = client_for(member)
    url = reverse("v1:deck-entry", args=[deck.uuid])
    r = c.post(url, {"card": str(cards[1].uuid), "zone": "main_deck", "quantity": 4}, format="json")
    assert r.status_code == 200
    assert r.data["zone_counts"]["main_deck"] == 4
    assert DeckEntry.objects.filter(version=deck.current_version, card=cards[1]).exists()

    # quantity 0 removes
    r2 = c.post(url, {"card": str(cards[1].uuid), "zone": "main_deck", "quantity": 0}, format="json")
    assert r2.data["zone_counts"]["main_deck"] == 0


def test_copy_limit_flagged_by_validate(member, deck, cards):
    c = client_for(member)
    url = reverse("v1:deck-entry", args=[deck.uuid])
    c.post(url, {"card": str(cards[1].uuid), "zone": "main_deck", "quantity": 5}, format="json")
    v = c.get(reverse("v1:deck-validate", args=[deck.uuid]))
    assert v.status_code == 200
    assert v.data["is_valid"] is False
    assert any(e["code"] == "COPY_LIMIT" for e in v.data["errors"])


def test_publish_makes_public(member, deck):
    c = client_for(member)
    r = c.post(reverse("v1:deck-publish", args=[deck.uuid]), {"visibility": "public"}, format="json")
    assert r.data["visibility"] == "public"
    deck.refresh_from_db()
    assert deck.visibility == "public"


def test_private_deck_hidden_from_others(member, other_member, deck):
    other = client_for(other_member)
    resp = other.get(reverse("v1:deck-detail", args=[deck.uuid]))
    assert resp.status_code == 403


def test_public_deck_visible_and_forkable(member, other_member, deck, cards):
    owner = client_for(member)
    owner.post(reverse("v1:deck-entry", args=[deck.uuid]),
               {"card": str(cards[2].uuid), "zone": "main_deck", "quantity": 3}, format="json")
    owner.post(reverse("v1:deck-publish", args=[deck.uuid]), {"visibility": "public"}, format="json")

    other = client_for(other_member)
    assert other.get(reverse("v1:deck-detail", args=[deck.uuid])).status_code == 200

    fork = other.post(reverse("v1:deck-fork", args=[deck.uuid]))
    assert fork.status_code == 201
    forked = Deck.objects.get(uuid=fork.data["uuid"])
    assert forked.owner == other_member
    assert forked.forked_from_id == deck.id
    assert forked.current_version.entries.count() == 1  # copied entry


def test_check_banlist_link_drives_validation(member, deck, cards):
    """Selecting a banlist on the deck makes validate flag its banned cards —
    without a query param, and without changing the deck's cards."""
    from apps.banlists.choices import BanlistCategory, RestrictionType
    from apps.banlists.models import Banlist, BanlistEntry, BanlistVersion

    bl = Banlist.objects.create(name="B", category=BanlistCategory.COMMUNITY,
                                format_code="standard")
    bv = BanlistVersion.objects.create(banlist=bl, version=1)
    bl.current_version = bv
    bl.save()
    BanlistEntry.objects.create(version=bv, restriction_type=RestrictionType.BANNED, card=cards[0])

    c = client_for(member)
    c.post(reverse("v1:deck-entry", args=[deck.uuid]),
           {"card": str(cards[0].uuid), "zone": "main_deck", "quantity": 1}, format="json")

    # No banlist selected → no BANNED error.
    v0 = c.get(reverse("v1:deck-validate", args=[deck.uuid])).data
    assert not any(e["code"] == "BANNED_CARD" for e in v0["errors"])

    # Link the banlist to the deck, then validate again (no query param).
    c.patch(reverse("v1:deck-detail", args=[deck.uuid]),
            {"check_banlist_uuid": str(bl.uuid)}, format="json")
    v1 = c.get(reverse("v1:deck-validate", args=[deck.uuid])).data
    assert any(e["code"] == "BANNED_CARD" for e in v1["errors"])

    # The restriction map exposes the banned card for the builder.
    rm = c.get(reverse("v1:banlist-restriction-map", args=[bl.uuid])).data
    assert rm["restrictions"][str(cards[0].uuid)]["type"] == "banned"


def test_cannot_edit_others_deck(member, other_member, deck, cards):
    other = client_for(other_member)
    r = other.post(reverse("v1:deck-entry", args=[deck.uuid]),
                   {"card": str(cards[0].uuid), "zone": "main_deck", "quantity": 1}, format="json")
    assert r.status_code == 403


def test_original_deck_edit_does_not_change_snapshot(member, deck, cards):
    c = client_for(member)
    entry_url = reverse("v1:deck-entry", args=[deck.uuid])
    c.post(entry_url, {"card": str(cards[1].uuid), "zone": "main_deck", "quantity": 2}, format="json")
    snap = c.post(reverse("v1:deck-snapshot", args=[deck.uuid]))
    hash_before = snap.data["content_hash"]
    # edit the deck afterwards
    c.post(entry_url, {"card": str(cards[3].uuid), "zone": "main_deck", "quantity": 2}, format="json")
    from apps.decks.models import DeckSnapshot
    stored = DeckSnapshot.objects.get(uuid=snap.data["uuid"])
    assert stored.content_hash == hash_before  # snapshot immutable


def test_set_cover_via_printing_and_card_and_clear(member, deck, cards):
    c = client_for(member)
    url = reverse("v1:deck-set-cover", args=[deck.uuid])
    pr = cards[1].printings.first()
    # via printing uuid
    r = c.post(url, {"printing": str(pr.uuid)}, format="json")
    assert r.status_code == 200
    assert r.data["cover_printing_uuid"] == str(pr.uuid)
    deck.refresh_from_db()
    assert deck.cover_printing_id == pr.id
    # via card uuid (resolves to its printing)
    r2 = c.post(url, {"card": str(cards[2].uuid)}, format="json")
    assert r2.data["cover_printing_uuid"] is not None
    # clear
    r3 = c.post(url, {"printing": None}, format="json")
    assert r3.data["cover_printing_uuid"] is None


def test_set_cover_requires_owner(member, other_member, deck):
    r = client_for(other_member).post(
        reverse("v1:deck-set-cover", args=[deck.uuid]), {"printing": None}, format="json")
    assert r.status_code == 403
