from rest_framework.routers import DefaultRouter

from .views import CardSetViewSet, CardViewSet

router = DefaultRouter()
router.register("cards", CardViewSet, basename="card")
router.register("sets", CardSetViewSet, basename="set")

urlpatterns = router.urls
