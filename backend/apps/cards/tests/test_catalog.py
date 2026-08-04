import pytest
from django.urls import reverse

from apps.cards.models import Card, CardPrinting, CardSet, normalize_name
from apps.imports.services import ImportRunner, ensure_source

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog(db):
    source = ensure_source("fixture", "Fixture")
    runner = ImportRunner(source, triggered_by="test")
    runner.import_sets()
    runner.import_cards()
    return source


def test_fixture_import_creates_catalog(catalog):
    assert CardSet.objects.count() == 3
    assert Card.objects.count() == 30
    assert CardPrinting.objects.count() == 30


def test_import_is_idempotent(catalog):
    runner = ImportRunner(catalog, triggered_by="test")
    runner.import_sets()
    batch = runner.import_cards()
    assert Card.objects.count() == 30
    assert CardPrinting.objects.count() == 30
    assert batch.created == 0
    assert batch.updated == 30


def test_normalize_name():
    assert normalize_name("Blazing Dragon, #1!") == "blazing dragon 1"


def test_card_list_public(api, catalog):
    resp = api.get(reverse("v1:card-list"))
    assert resp.status_code == 200
    assert resp.data["count"] == 30
    assert "default_printing" in resp.data["results"][0]


def test_card_search(api, catalog):
    resp = api.get(reverse("v1:card-list"), {"search": "Dragon"})
    assert resp.status_code == 200
    assert resp.data["count"] >= 1
    assert all("dragon" in r["name"].lower() for r in resp.data["results"])


def test_card_filter_by_grade(api, catalog):
    resp = api.get(reverse("v1:card-list"), {"grade": "0"})
    assert resp.status_code == 200
    assert all(r["grade"] == 0 for r in resp.data["results"])


def test_card_filter_is_trigger(api, catalog):
    resp = api.get(reverse("v1:card-list"), {"is_trigger": "true"})
    assert resp.status_code == 200
    assert all(r["trigger"] for r in resp.data["results"])


def test_card_detail_has_printings(api, catalog):
    card = Card.objects.first()
    resp = api.get(reverse("v1:card-detail", args=[card.slug]))
    assert resp.status_code == 200
    assert resp.data["name"] == card.name
    assert len(resp.data["printings"]) >= 1


def test_printings_of_same_card_share_identity(catalog):
    # A second printing of an existing card must not create a new Card identity.
    card = Card.objects.first()
    before = Card.objects.count()
    CardPrinting.objects.create(
        card=card, card_number="ALT-001",
        card_set=CardSet.objects.first(), language="jp",
    )
    assert Card.objects.count() == before  # identity unchanged
    assert card.printings.count() >= 2
