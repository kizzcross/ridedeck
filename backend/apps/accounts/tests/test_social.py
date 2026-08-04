import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import FavoriteCard, Friendship
from apps.cards.models import Card, CardSet

pytestmark = pytest.mark.django_db


def client_for(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture
def a_card(db):
    s = CardSet.objects.create(code="T", name="Test Set")
    c = Card.objects.create(name="Test Dragon", grade=3, card_type="normal_unit")
    c.printings.create(card_number="T-001", card_set=s)
    return c


# --- Referral ------------------------------------------------------------
def test_referral_registration_creates_friendship(api, member):
    code = member.profile.referral_code
    resp = api.post(
        reverse("v1:auth-register"),
        {"email": "ref@test.dev", "username": "refereed",
         "password": "s3cretpass!", "password_confirm": "s3cretpass!",
         "referral_code": code},
        format="json",
    )
    assert resp.status_code == 201
    from django.contrib.auth import get_user_model

    new_user = get_user_model().objects.get(username="refereed")
    assert new_user.profile.referred_by_id == member.id
    # They are already friends.
    assert new_user.id in Friendship.friend_ids(member)


def test_invalid_referral_code_is_ignored(api):
    resp = api.post(
        reverse("v1:auth-register"),
        {"email": "x@test.dev", "username": "noref",
         "password": "s3cretpass!", "password_confirm": "s3cretpass!",
         "referral_code": "BOGUS999"},
        format="json",
    )
    assert resp.status_code == 201


# --- Friend requests -----------------------------------------------------
def test_friend_request_and_accept_flow(member, other_member):
    m, o = client_for(member), client_for(other_member)
    resp = m.post(reverse("v1:friend-add"), {"username": other_member.username}, format="json")
    assert resp.status_code == 201
    assert resp.data["status"] == "pending"

    # other sees an incoming request
    reqs = o.get(reverse("v1:friend-requests")).data
    assert len(reqs["incoming"]) == 1
    uuid = reqs["incoming"][0]["uuid"]

    # accept
    assert o.post(reverse("v1:friend-accept", args=[uuid])).status_code == 200
    friends = o.get(reverse("v1:friend-friends")).data
    assert any(f["username"] == member.username for f in friends)


def test_mutual_request_auto_accepts(member, other_member):
    m, o = client_for(member), client_for(other_member)
    m.post(reverse("v1:friend-add"), {"username": other_member.username}, format="json")
    # other sends back → should accept
    resp = o.post(reverse("v1:friend-add"), {"username": member.username}, format="json")
    assert resp.status_code == 201
    assert resp.data["status"] == "accepted"


def test_cannot_add_self(member):
    m = client_for(member)
    resp = m.post(reverse("v1:friend-add"), {"username": member.username}, format="json")
    assert resp.status_code == 400


def test_reject_removes_request(member, other_member):
    m, o = client_for(member), client_for(other_member)
    m.post(reverse("v1:friend-add"), {"username": other_member.username}, format="json")
    uuid = o.get(reverse("v1:friend-requests")).data["incoming"][0]["uuid"]
    assert o.delete(reverse("v1:friend-detail", args=[uuid])).status_code == 204
    assert Friendship.objects.count() == 0


# --- Favorites -----------------------------------------------------------
def test_favorite_toggle(member, a_card):
    m = client_for(member)
    url = reverse("v1:me-favorites")
    r1 = m.post(url, {"card": str(a_card.uuid)}, format="json")
    assert r1.status_code == 201 and r1.data["favorited"] is True
    assert FavoriteCard.objects.filter(user=member, card=a_card).exists()

    r2 = m.post(url, {"card": str(a_card.uuid)}, format="json")
    assert r2.data["favorited"] is False
    assert not FavoriteCard.objects.filter(user=member, card=a_card).exists()


def test_favorites_list_and_ids(member, a_card):
    m = client_for(member)
    m.post(reverse("v1:me-favorites"), {"card": str(a_card.uuid)}, format="json")
    listing = m.get(reverse("v1:me-favorites")).data
    assert listing["count"] == 1
    ids = m.get(reverse("v1:me-favorite-ids")).data
    assert str(a_card.uuid) in ids["card_uuids"]


# --- Avatar --------------------------------------------------------------
def test_avatar_options_and_set(member):
    m = client_for(member)
    opts = m.get(reverse("v1:avatar-options")).data
    assert len(opts["options"]) == 11
    resp = m.patch(reverse("v1:me-profile"), {"avatar_key": "nation:dragon_empire"}, format="json")
    assert resp.status_code == 200
    member.profile.refresh_from_db()
    assert member.profile.avatar_key == "nation:dragon_empire"


def test_admin_can_promote_and_demote(platform_admin, member):
    admin = client_for(platform_admin)
    r = admin.post(reverse("v1:admin-promote-user"), {"username": member.username}, format="json")
    assert r.status_code == 200
    member.refresh_from_db()
    assert member.is_platform_admin is True
    # audit recorded
    from apps.common.models import AuditLog
    assert AuditLog.objects.filter(action="admin_action").exists()
    # demote back
    r2 = admin.post(reverse("v1:admin-promote-user"),
                    {"username": member.username, "promote": False}, format="json")
    assert r2.data["role"] == "member"


def test_non_admin_cannot_promote(member, other_member):
    r = client_for(member).post(reverse("v1:admin-promote-user"),
                                {"username": other_member.username}, format="json")
    assert r.status_code == 403


def test_admin_cannot_demote_self(platform_admin):
    r = client_for(platform_admin).post(reverse("v1:admin-promote-user"),
                                        {"username": platform_admin.username, "promote": False},
                                        format="json")
    assert r.status_code == 400


def test_public_profile_shows_friendship_state(member, other_member):
    m = client_for(member)
    m.post(reverse("v1:friend-add"), {"username": other_member.username}, format="json")
    data = m.get(reverse("v1:public-profile", args=[other_member.username])).data
    assert data["friendship_state"] == "outgoing"
    assert data["friendship_uuid"]
