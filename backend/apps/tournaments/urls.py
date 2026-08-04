from rest_framework.routers import DefaultRouter

from .views import MatchViewSet, TournamentViewSet

router = DefaultRouter()
router.register("tournaments", TournamentViewSet, basename="tournament")
router.register("matches", MatchViewSet, basename="match")

urlpatterns = router.urls
