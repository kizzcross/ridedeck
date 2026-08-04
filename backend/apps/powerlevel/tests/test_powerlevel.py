import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.cards.models import Card, CardPrinting, CardSet
from apps.common.models import AuditLog
from apps.powerlevel.models import CardPowerLevel, CardPowerLevelHistory
from apps.powerlevel.services import deck_power_stats, set_power_level

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
        card = Card.objects.create(name=f"Card {i}", grade=i, card_type="normal_unit")
        CardPrinting.objects.create(card_number=f"S-{i:03d}", card_set=s, card=card)
        made.append(card)
    return made


# --- Acceptance-critical permission tests --------------------------------
def test_member_cannot_set_power_level(member, cards):
    c = client_for(member)
    r = c.post(reverse("v1:admin-power-set"),
               {"card": str(cards[0].uuid), "format_code": "standard", "value": 8,
                "justification": "x"}, format="json")
    assert r.status_code == 403
    assert not CardPowerLevel.objects.exists()


def test_organizer_cannot_set_power_level(organizer, cards):
    # Tournament Organizer is just a member globally → also 403.
    c = client_for(organizer)
    r = c.post(reverse("v1:admin-power-set"),
               {"card": str(cards[0].uuid), "format_code": "standard", "value": 8,
                "justification": "x"}, format="json")
    assert r.status_code == 403


def test_platform_admin_sets_power_level_with_justification(platform_admin, cards):
    c = client_for(platform_admin)
    r = c.post(reverse("v1:admin-power-set"),
               {"card": str(cards[0].uuid), "format_code": "standard", "value": 8,
                "justification": "Dominante no meta atual."}, format="json")
    assert r.status_code == 201
    pl = CardPowerLevel.objects.get(card=cards[0], format_code="standard")
    assert pl.value == 8 and pl.updated_by == platform_admin


def test_justification_required(platform_admin, cards):
    c = client_for(platform_admin)
    r = c.post(reverse("v1:admin-power-set"),
               {"card": str(cards[0].uuid), "format_code": "standard", "value": 8},
               format="json")
    assert r.status_code == 400  # justification missing


def test_power_change_creates_history_and_audit(platform_admin, cards):
    set_power_level(admin=platform_admin, card=cards[0], format_code="standard",
                    value=5, justification="v1")
    set_power_level(admin=platform_admin, card=cards[0], format_code="standard",
                    value=8, justification="bump")
    hist = CardPowerLevelHistory.objects.filter(card=cards[0], format_code="standard").order_by("version")
    assert list(hist.values_list("previous_value", "new_value")) == [(None, 5), (5, 8)]
    assert AuditLog.objects.filter(action="power_level_change").count() == 2


def test_same_card_different_power_per_format(platform_admin, cards):
    set_power_level(admin=platform_admin, card=cards[0], format_code="standard",
                    value=8, justification="std")
    set_power_level(admin=platform_admin, card=cards[0], format_code="premium",
                    value=5, justification="prem")
    assert CardPowerLevel.objects.get(card=cards[0], format_code="standard").value == 8
    assert CardPowerLevel.objects.get(card=cards[0], format_code="premium").value == 5


def test_bulk_set_admin_only(member, platform_admin, cards):
    payload = {"cards": [str(c.uuid) for c in cards], "format_code": "standard",
               "value": 6, "justification": "bulk"}
    assert client_for(member).post(reverse("v1:admin-power-bulk"), payload, format="json").status_code == 403
    r = client_for(platform_admin).post(reverse("v1:admin-power-bulk"), payload, format="json")
    assert r.status_code == 201 and r.data["updated"] == 4


# --- Deck power calculation ----------------------------------------------
def test_deck_power_stats(platform_admin, cards):
    from apps.decks.models import Deck
    from apps.decks.services import ensure_working_version, set_entry

    for card, v in zip(cards, [5, 7, 9, 6], strict=False):
        set_power_level(admin=platform_admin, card=card, format_code="standard",
                        value=v, justification="x")
    deck = Deck.objects.create(owner=platform_admin, title="D", format_code="standard")
    version = ensure_working_version(deck)
    set_entry(version, cards[0], "main_deck", 4)   # 5×4
    set_entry(version, cards[2], "main_deck", 2)   # 9×2

    stats = deck_power_stats(version, "standard")
    assert stats["has_data"] is True
    assert stats["max_power_level"] == 9
    assert stats["weighted_sum"] == 5 * 4 + 9 * 2
    assert stats["count_at_or_above"]["9"] == 2
