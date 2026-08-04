"""Same-origin image proxy for card art.

Card images live on third-party CDNs (TCGplayer, Fandom) that don't send CORS
headers, so a browser can't read their pixels back off a <canvas>. That breaks
client-side "export deck as image". This view re-serves whitelisted image hosts
from our own origin so the export capture is untainted.

It is deliberately narrow: only https, only known image hosts, no redirects,
a hard size cap and a short timeout — i.e. not an open proxy (no SSRF surface).
"""
from urllib.parse import urlparse

import requests
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View

# Hosts we are willing to re-serve. Suffix match so CDN shards are covered.
_ALLOWED_HOST_SUFFIXES = (
    "tcgplayer-cdn.tcgplayer.com",
    ".tcgplayer.com",
    "static.wikia.nocookie.net",
    ".fandom.com",
)
_MAX_BYTES = 4 * 1024 * 1024  # 4 MB is plenty for a card thumbnail
_TIMEOUT = 8


def _host_allowed(host: str) -> bool:
    host = host.lower()
    return any(
        host == suffix or host.endswith(suffix)
        for suffix in _ALLOWED_HOST_SUFFIXES
    )


class CardImageProxyView(View):
    """GET /cards/img/?u=<https image url> → the image bytes, same-origin."""

    def get(self, request, *args, **kwargs):
        url = request.GET.get("u", "")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not _host_allowed(parsed.netloc):
            return HttpResponseBadRequest("URL não permitida.")

        cache_key = f"imgproxy:{url}"
        cached = cache.get(cache_key)
        if cached:
            body, content_type = cached
        else:
            try:
                resp = requests.get(url, timeout=_TIMEOUT, stream=True,
                                    allow_redirects=False)
            except requests.RequestException:
                return HttpResponse(status=502)
            if resp.status_code != 200:
                return HttpResponse(status=resp.status_code)
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            if not content_type.startswith("image/"):
                return HttpResponseBadRequest("Não é uma imagem.")
            body = b""
            for chunk in resp.iter_content(64 * 1024):
                body += chunk
                if len(body) > _MAX_BYTES:
                    return HttpResponseBadRequest("Imagem muito grande.")
            cache.set(cache_key, (body, content_type), 60 * 60 * 24)

        response = HttpResponse(body, content_type=content_type)
        response["Cache-Control"] = "public, max-age=86400"
        response["Access-Control-Allow-Origin"] = "*"
        return response
