import pytest
from django.urls import reverse

from apps.cards.models import Card
from apps.imports.models import ImportBatch, RawImportPayload
from apps.imports.services import ImportRunner, ensure_source

pytestmark = pytest.mark.django_db


def test_raw_payload_is_persisted():
    source = ensure_source("fixture", "Fixture")
    runner = ImportRunner(source, triggered_by="test")
    runner.import_sets()
    runner.import_cards()
    assert RawImportPayload.objects.filter(endpoint="products").count() == 30
    assert RawImportPayload.objects.filter(endpoint="sets").count() == 3


def test_batch_records_metrics_and_audit():
    source = ensure_source("fixture", "Fixture")
    runner = ImportRunner(source, triggered_by="test")
    batch = runner.import_cards()
    assert batch.status == ImportBatch.Status.SUCCESS
    assert batch.processed == 30
    assert batch.created == 30


def test_trigger_import_requires_admin(auth_api):
    # Normal member cannot trigger imports.
    resp = auth_api.post(reverse("v1:import-batch-trigger"),
                         {"source_key": "fixture", "kind": "full"}, format="json")
    assert resp.status_code == 403


def test_admin_can_trigger_import(admin_api):
    ensure_source("fixture", "Fixture")
    resp = admin_api.post(reverse("v1:import-batch-trigger"),
                          {"source_key": "fixture", "kind": "full"}, format="json")
    assert resp.status_code == 201
    assert Card.objects.count() == 30


def test_data_source_crud_admin_only(member, platform_admin):
    from rest_framework.test import APIClient

    member_client = APIClient()
    member_client.force_authenticate(user=member)
    admin_client = APIClient()
    admin_client.force_authenticate(user=platform_admin)

    assert member_client.get(reverse("v1:data-source-list")).status_code == 403
    assert admin_client.get(reverse("v1:data-source-list")).status_code == 200
