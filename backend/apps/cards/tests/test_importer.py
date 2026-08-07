import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from apps.banlists.importer import parse_banlist
from apps.banlists.models import Banlist
from apps.cards.importer import parse_card_list, resolve_one
from apps.cards.models import Card, CardPrinting, CardSet
from apps.decks.models import Deck

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog(db):
    s = CardSet.objects.create(code="BT01", name="Set 01")
    made = {}
    for i, name in enumerate(["Dragonic Overlord", "Blaster Blade", "Chronojet Dragon",
                              "Nightrose", "Bruce Ranindra"]):
        c = Card.objects.create(name=name, grade=i % 4, card_type="normal_unit",
                                nation="dragon_empire")
        CardPrinting.objects.create(card_number=f"BT01/{i + 1:03d}", card_set=s, card=c, price="1.00")
        made[name] = c
    return made


def client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


# --- Parser: many formats -------------------------------------------------
def test_parser_handles_many_formats():
    text = """
    Main Deck:
    4x Dragonic Overlord
    4 Blaster Blade
    Chronojet Dragon x2
    Nightrose (3)
    Bruce Ranindra
    # a comment
    Ride Deck
    2, Blaster Blade
    G Zone
    Dragonic Overlord (BT01/001)
    """
    lines = parse_card_list(text)
    by_name = {}
    for ln in lines:
        by_name.setdefault(ln.name, ln)   # keep first occurrence
    assert by_name["Dragonic Overlord"].quantity == 4
    assert by_name["Blaster Blade"].quantity in (2, 4)  # appears twice
    assert by_name["Chronojet Dragon"].quantity == 2
    assert by_name["Nightrose"].quantity == 3
    assert by_name["Bruce Ranindra"].quantity == 1
    # Zone headers switched the zone.
    zones = {ln.name: ln.zone for ln in lines}
    assert zones["Bruce Ranindra"] == "main_deck"
    assert any(ln.zone == "ride_deck" for ln in lines)
    assert any(ln.zone == "g_deck" for ln in lines)
    # Card number was extracted.
    assert any(ln.card_number and "BT01/001" in ln.card_number for ln in lines)


# --- Fuzzy resolution -----------------------------------------------------
def test_fuzzy_resolves_typo(catalog):
    r = resolve_one("Dragonic Overlrd")   # missing an 'o'
    assert r.card == catalog["Dragonic Overlord"]
    assert r.confidence in ("fuzzy", "exact")


def test_exact_and_code_resolution(catalog):
    assert resolve_one("blaster blade").confidence == "exact"   # normalized
    assert resolve_one("Anything", "BT01/003").card == catalog["Chronojet Dragon"]


def test_unmatched_is_flagged(catalog):
    r = resolve_one("Zzzq Wxyv Nonsense")
    assert r.card is None or r.confidence in ("ambiguous", "unmatched")


# --- Deck import endpoints ------------------------------------------------
def test_deck_import_preview_and_apply(member, catalog):
    c = client_for(member)
    preview = c.post(reverse("v1:deck-import-preview"),
                     {"text": "4 Dragonic Overlrd\n2 Blaster Blade"}, format="json")
    assert preview.status_code == 200
    lines = preview.data["lines"]
    assert lines[0]["card"]["name"] == "Dragonic Overlord"   # typo fixed
    assert lines[0]["quantity"] == 4

    deck = Deck.objects.create(owner=member, title="Imported", format_code="standard")
    payload = {"replace": True, "lines": [
        {"card": ln["card"]["uuid"], "zone": ln["zone"], "quantity": ln["quantity"]}
        for ln in lines if ln["card"]
    ]}
    r = c.post(reverse("v1:deck-import-list", args=[deck.uuid]), payload, format="json")
    assert r.status_code == 200
    qtys = {e["card"]["name"]: e["quantity"] for e in r.data["entries"]}
    assert qtys["Dragonic Overlord"] == 4
    assert qtys["Blaster Blade"] == 2


def test_deck_import_requires_owner(member, other_member, catalog):
    deck = Deck.objects.create(owner=member, title="D", format_code="standard")
    r = client_for(other_member).post(
        reverse("v1:deck-import-list", args=[deck.uuid]),
        {"lines": [], "replace": True}, format="json")
    assert r.status_code == 403


# --- Banlist import -------------------------------------------------------
def test_banlist_parser_reads_limits(catalog):
    entries = parse_banlist("0 Dragonic Overlord\n1 Blaster Blade\n2 Chronojet Dragon")
    by_name = {e.input_name: e for e in entries}
    assert by_name["Dragonic Overlord"].restriction_type == "banned"
    assert by_name["Blaster Blade"].restriction_type == "limit_to_1"
    assert by_name["Chronojet Dragon"].restriction_type == "limit_to_2"


def test_banlist_import_applies_entries(member, catalog):
    c = client_for(member)
    bl = Banlist.objects.create(owner=member, name="My banlist", format_code="standard")
    text = "Banned\nDragonic Overlrd\nLimited to 1\nBlaster Blade"
    preview = c.post(reverse("v1:banlist-import-preview"), {"text": text}, format="json")
    assert preview.status_code == 200
    entries = [
        {"card": e["card"]["uuid"], "restriction_type": e["restriction_type"],
         "limit_value": e["limit_value"]}
        for e in preview.data["entries"] if e["card"]
    ]
    r = c.post(reverse("v1:banlist-import-list", args=[bl.uuid]),
               {"entries": entries, "replace": True}, format="json")
    assert r.status_code == 200
    kinds = {row["restriction_type"] for row in r.data["entries"]}
    assert "banned" in kinds and "limit_to_1" in kinds
