from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django.views import View
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses={200: dict})
    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:  # pragma: no cover
            db_ok = False
        return Response({"status": "ok", "database": db_ok})


class SPAIndexView(View):
    """Serve the built SPA's index.html for client-side routes (production).
    WhiteNoise serves the hashed assets; this handles deep links like /app/decks."""

    _cache: str | None = None

    def get(self, request, *args, **kwargs):
        if SPAIndexView._cache is None:
            index = settings.FRONTEND_DIST_DIR / "index.html"
            if not index.exists():
                return HttpResponse(
                    "Frontend build not found. Run the Vite build and mount it at "
                    "backend/frontend_dist/.",
                    status=503,
                )
            SPAIndexView._cache = index.read_text(encoding="utf-8")
        return HttpResponse(SPAIndexView._cache, content_type="text/html")
