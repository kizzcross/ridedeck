"""Root URL configuration — versioned API under /api/v1/."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

api_v1 = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.cards.urls")),
    path("", include("apps.collection.urls")),
    path("", include("apps.formats.urls")),
    path("", include("apps.powerlevel.urls")),
    path("", include("apps.banlists.urls")),
    path("", include("apps.decks.urls")),
    path("", include("apps.collection.urls")),
    path("", include("apps.tournaments.urls")),
    path("", include("apps.imports.urls")),
    path("", include("apps.community.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include((api_v1, "v1"), namespace="v1")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("healthz/", include("apps.common.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve the built SPA for all non-API/admin routes (production).
if settings.SERVE_SPA:
    from django.urls import re_path

    from apps.common.views import SPAIndexView

    urlpatterns += [
        re_path(r"^(?!api/|admin/|static/|media/|healthz/).*$", SPAIndexView.as_view()),
    ]
