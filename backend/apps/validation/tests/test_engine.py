import pytest
from django.core.management import call_command

from apps.cards.models import Card, CardPrinting, CardSet
from apps.decks.models import Deck
from apps.decks.services import ensure_working_version, set_entry
from apps.validation.service import validate_deck_version

pytestmark = pytest.mark.django_db


@pytest.fixture
def formats(db):
    call_command("seed_formats")


@pytest.fixture
def cards(db):
    s = CardSet.objects.create(code="S", name="Set")
    made = []
    for i in range(6):
        card = Card.objects.create(
            name=f"Card {i}", grade=i % 4, card_type="normal_unit",
            trigger="critical" if i == 0 else "", nation="dragon_empire",
        )
        CardPrinting.objects.create(card_number=f"S-{i:03d}", card_set=s, card=card)
        made.append(card)
    return made


def test_engine_uses_db_format_rules(formats, cards):
    deck = Deck.objects.create(owner_id=_owner(), title="D", format_code="standard")
    version = ensure_working_version(deck)
    set_entry(version, cards[1], "main_deck", 2)
    result = validate_deck_version(version)
    assert result["format_rules_version"] == 1
    # main deck too small → zone count error
    assert any(e["code"] == "MAIN_DECK_COUNT" for e in result["errors"])


def test_copy_limit_from_construction_rule(formats, cards):
    deck = Deck.objects.create(owner_id=_owner(), title="D", format_code="standard")
    version = ensure_working_version(deck)
    set_entry(version, cards[1], "main_deck", 5)  # over the 4-copy limit
    result = validate_deck_version(version)
    assert any(e["code"] == "COPY_LIMIT" for e in result["errors"])


def test_missing_owned_is_warning_not_error(formats, cards):
    deck = Deck.objects.create(owner_id=_owner(), title="D", format_code="standard")
    version = ensure_working_version(deck)
    set_entry(version, cards[1], "main_deck", 4)
    result = validate_deck_version(version, owned_map={str(cards[1].uuid): 1})
    assert any(w["code"] == "MISSING_OWNED_COPIES" for w in result["warnings"])
    assert not any("OWNED" in e["code"] for e in result["errors"])


def test_multiple_nations_flagged(formats, cards):
    cards[2].nation = "dark_states"
    cards[2].save()
    deck = Deck.objects.create(owner_id=_owner(), title="D", format_code="standard")
    version = ensure_working_version(deck)
    set_entry(version, cards[1], "main_deck", 4)
    set_entry(version, cards[2], "main_deck", 4)
    result = validate_deck_version(version)
    assert any(e["code"] == "MULTIPLE_NATIONS" for e in result["errors"])


def _owner():
    from django.contrib.auth import get_user_model
    u, _ = get_user_model().objects.get_or_create(
        email="o@t.dev", defaults={"username": "o"})
    return u.id
