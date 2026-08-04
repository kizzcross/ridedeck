from rest_framework.routers import DefaultRouter

from .views import DeckViewSet

router = DefaultRouter()
router.register("decks", DeckViewSet, basename="deck")

urlpatterns = router.urls
