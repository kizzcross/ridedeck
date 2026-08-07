import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.decks.models import Deck

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", email="a@x.com", password="pw123456")


@pytest.fixture
def other(db):
    return User.objects.create_user(username="bob", email="b@x.com", password="pw123456")


@pytest.fixture
def deck(db, user):
    return Deck.objects.create(owner=user, title="T", format_code="standard")


def auth(client, u):
    client.force_authenticate(u)
    return client


def test_comment_create_list_and_delete(deck, user, other):
    c = auth(APIClient(), user)

    # Create a comment on the deck.
    r = c.post("/api/v1/comments/", {
        "target_type": "deck", "target_uuid": str(deck.uuid), "body": "nice deck",
    }, format="json")
    assert r.status_code == 201, r.content
    comment_uuid = r.data["uuid"]
    assert r.data["can_delete"] is True

    # Anyone can read the thread by target.
    other_client = auth(APIClient(), other)
    r = other_client.get(f"/api/v1/comments/?target_type=deck&target_uuid={deck.uuid}")
    assert r.status_code == 200
    assert r.data["count"] == 1
    assert r.data["results"][0]["can_delete"] is False  # bob is not the author

    # A non-author cannot delete.
    r = other_client.delete(f"/api/v1/comments/{comment_uuid}/")
    assert r.status_code == 403

    # The author can delete (soft delete → disappears from thread).
    r = c.delete(f"/api/v1/comments/{comment_uuid}/")
    assert r.status_code == 204
    r = c.get(f"/api/v1/comments/?target_type=deck&target_uuid={deck.uuid}")
    assert r.data["count"] == 0


def test_comment_rejects_unknown_target(user):
    c = auth(APIClient(), user)
    r = c.post("/api/v1/comments/", {
        "target_type": "deck",
        "target_uuid": "00000000-0000-0000-0000-000000000000",
        "body": "ghost",
    }, format="json")
    assert r.status_code == 400


def test_comment_requires_auth_to_post(deck):
    r = APIClient().post("/api/v1/comments/", {
        "target_type": "deck", "target_uuid": str(deck.uuid), "body": "hi",
    }, format="json")
    assert r.status_code in (401, 403)
