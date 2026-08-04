from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CollectionViewSet,
    TradeDeleteView,
    TradeView,
    WishlistDeleteView,
    WishlistView,
)

router = DefaultRouter()
router.register("collection", CollectionViewSet, basename="collection")

urlpatterns = [
    path("wishlist/", WishlistView.as_view(), name="wishlist"),
    path("wishlist/<uuid:uuid>/", WishlistDeleteView.as_view(), name="wishlist-delete"),
    path("trade/", TradeView.as_view(), name="trade"),
    path("trade/<uuid:uuid>/", TradeDeleteView.as_view(), name="trade-delete"),
    *router.urls,
]
