import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.cards.models import Card, CardPrinting, CardSet
from apps.collection.models import UserCollectionItem
from apps.collection.services import owned_map
from apps.decks.models import Deck
from apps.decks.services import ensure_working_version, set_entry

pytestmark = pytest.mark.django_db


def client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def catalog(db):
    s = CardSet.objects.create(code="S", name="Set")
    cards = []
    for i in range(3):
        card = Card.objects.create(name=f"Card {i}", grade=i, card_type="normal_unit")
        CardPrinting.objects.create(card_number=f"S-{i:03d}", card_set=s, card=card, price="2.50")
        cards.append(card)
    return cards


def test_set_owned_and_aggregate(member, catalog):
    c = client_for(member)
    printing = catalog[0].printings.first()
    r = c.post(reverse("v1:collection-set-owned"),
               {"printing": str(printing.uuid), "quantity": 2}, format="json")
    assert r.status_code == 200
    assert r.data["owned"] == 2
    assert owned_map(member)[str(catalog[0].uuid)] == 2
    # setting to 0 removes
    c.post(reverse("v1:collection-set-owned"),
           {"printing": str(printing.uuid), "quantity": 0}, format="json")
    assert not UserCollectionItem.objects.filter(user=member, card=catalog[0]).exists()


def test_owned_map_endpoint(member, catalog):
    c = client_for(member)
    p = catalog[1].printings.first()
    c.post(reverse("v1:collection-set-owned"), {"printing": str(p.uuid), "quantity": 3}, format="json")
    data = c.get(reverse("v1:collection-owned-map-view")).data
    assert data["owned"][str(catalog[1].uuid)] == 3


def test_collection_never_invalidates_deck(member, catalog):
    """The golden rule: using more copies than owned is a report indicator,
    never a validation error."""
    c = client_for(member)
    deck = Deck.objects.create(owner=member, title="D", format_code="standard")
    version = ensure_working_version(deck)
    set_entry(version, catalog[0], "main_deck", 4)  # use 4
    # own only 1
    p = catalog[0].printings.first()
    c.post(reverse("v1:collection-set-owned"), {"printing": str(p.uuid), "quantity": 1}, format="json")

    validation = c.get(reverse("v1:deck-validate", args=[deck.uuid])).data
    # No error mentions ownership; missing copies must NOT appear as errors.
    assert not any("owned" in e.get("code", "").lower() or "copies" in e.get("message", "").lower()
                   for e in validation["errors"])

    report = c.get(reverse("v1:deck-collection-report", args=[deck.uuid])).data
    assert report["summary"]["used"] == 4
    assert report["summary"]["owned"] == 1
    assert report["summary"]["missing"] == 3
    assert report["summary"]["owned_pct"] == 25
    assert len(report["shopping_list"]) == 1
    assert report["shopping_list"][0]["missing"] == 3


def test_wishlist_add_and_delete(member, catalog):
    c = client_for(member)
    r = c.post(reverse("v1:wishlist"), {"card_uuid": str(catalog[2].uuid), "priority": 3}, format="json")
    assert r.status_code == 201
    uuid = r.data["uuid"]
    assert c.get(reverse("v1:wishlist")).data["count"] == 1
    assert c.delete(reverse("v1:wishlist-delete", args=[uuid])).status_code == 204


def test_collection_requires_auth(api):
    assert api.get(reverse("v1:collection-list")).status_code == 401
