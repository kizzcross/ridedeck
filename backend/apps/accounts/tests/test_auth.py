import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.choices import PlatformRole

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_register_creates_member_with_profile_and_preference(api):
    resp = api.post(
        reverse("v1:auth-register"),
        {"email": "New@Test.dev", "username": "newbie",
         "password": "s3cretpass!", "password_confirm": "s3cretpass!"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    user = User.objects.get(username="newbie")
    assert user.email == "new@test.dev"  # normalized/lowercased
    assert user.role == PlatformRole.MEMBER
    assert not user.is_platform_admin
    assert hasattr(user, "profile")
    assert hasattr(user, "preference")


def test_register_cannot_self_assign_admin_role(api):
    # Even if a client tries to inject role/is_superuser, it is ignored.
    resp = api.post(
        reverse("v1:auth-register"),
        {"email": "sneaky@test.dev", "username": "sneaky",
         "password": "s3cretpass!", "password_confirm": "s3cretpass!",
         "role": "platform_admin", "is_superuser": True},
        format="json",
    )
    assert resp.status_code == 201
    user = User.objects.get(username="sneaky")
    assert user.role == PlatformRole.MEMBER
    assert user.is_superuser is False


def test_password_mismatch_rejected(api):
    resp = api.post(
        reverse("v1:auth-register"),
        {"email": "x@test.dev", "username": "x",
         "password": "s3cretpass!", "password_confirm": "different!"},
        format="json",
    )
    assert resp.status_code == 400


def test_login_returns_jwt_and_me_works(api, member):
    resp = api.post(reverse("v1:auth-login"),
                    {"email": "member@test.dev", "password": "pass12345"}, format="json")
    assert resp.status_code == 200
    access = resp.data["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    me = api.get(reverse("v1:me"))
    assert me.status_code == 200
    assert me.data["username"] == "member"
    assert me.data["is_platform_admin"] is False


def test_me_requires_auth(api):
    assert api.get(reverse("v1:me")).status_code == 401


def test_promote_to_platform_admin(member):
    assert member.is_platform_admin is False
    member.promote_to_platform_admin()
    member.refresh_from_db()
    assert member.is_platform_admin is True
    assert member.role == PlatformRole.PLATFORM_ADMIN


def test_me_role_is_read_only(auth_api, member):
    # PATCH attempting to change role must not elevate.
    resp = auth_api.patch(reverse("v1:me"), {"role": "platform_admin"}, format="json")
    assert resp.status_code == 200
    member.refresh_from_db()
    assert member.role == PlatformRole.MEMBER
