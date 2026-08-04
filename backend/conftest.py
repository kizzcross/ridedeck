"""Shared pytest fixtures for the whole backend."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api() -> APIClient:
    return APIClient()


@pytest.fixture
def member(db):
    return User.objects.create_user(
        email="member@test.dev", username="member", password="pass12345"
    )


@pytest.fixture
def other_member(db):
    return User.objects.create_user(
        email="other@test.dev", username="other", password="pass12345"
    )


@pytest.fixture
def organizer(db):
    return User.objects.create_user(
        email="organizer@test.dev", username="organizer", password="pass12345"
    )


@pytest.fixture
def platform_admin(db):
    return User.objects.create_superuser(
        email="admin@test.dev", username="admin", password="pass12345"
    )


@pytest.fixture
def auth_api(api, member):
    api.force_authenticate(user=member)
    return api


@pytest.fixture
def admin_api(api, platform_admin):
    api.force_authenticate(user=platform_admin)
    return api
