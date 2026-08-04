from rest_framework.routers import DefaultRouter

from .views import GameFormatViewSet

router = DefaultRouter()
router.register("formats", GameFormatViewSet, basename="format")

urlpatterns = router.urls
