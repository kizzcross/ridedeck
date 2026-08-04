from rest_framework.routers import DefaultRouter

from .views import BanlistViewSet

router = DefaultRouter()
router.register("banlists", BanlistViewSet, basename="banlist")

urlpatterns = router.urls
