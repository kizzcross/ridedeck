import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_image_proxy_rejects_non_https():
    r = APIClient().get("/api/v1/cards/img/?u=http://tcgplayer-cdn.tcgplayer.com/x.jpg")
    assert r.status_code == 400


@pytest.mark.django_db
def test_image_proxy_rejects_disallowed_host():
    r = APIClient().get("/api/v1/cards/img/?u=https://evil.example.com/x.jpg")
    assert r.status_code == 400


@pytest.mark.django_db
def test_image_proxy_rejects_internal_host_ssrf():
    r = APIClient().get("/api/v1/cards/img/?u=https://169.254.169.254/latest/meta-data/")
    assert r.status_code == 400


@pytest.mark.django_db
def test_image_proxy_allows_whitelisted_host(monkeypatch):
    import apps.cards.views_media as vm

    class _Resp:
        status_code = 200
        headers = {"Content-Type": "image/jpeg"}

        def iter_content(self, _n):
            yield b"\xff\xd8\xff"  # jpeg magic bytes

    monkeypatch.setattr(vm.requests, "get", lambda *a, **k: _Resp())
    r = APIClient().get(
        "/api/v1/cards/img/?u=https://tcgplayer-cdn.tcgplayer.com/product/1_200w.jpg"
    )
    assert r.status_code == 200
    assert r["Content-Type"] == "image/jpeg"
    assert r["Access-Control-Allow-Origin"] == "*"
