from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CardSetViewSet, CardViewSet
from .views_media import CardImageProxyView

router = DefaultRouter()
router.register("cards", CardViewSet, basename="card")
router.register("sets", CardSetViewSet, basename="set")

urlpatterns = [
    path("cards/img/", CardImageProxyView.as_view(), name="card-image-proxy"),
    *router.urls,
]
