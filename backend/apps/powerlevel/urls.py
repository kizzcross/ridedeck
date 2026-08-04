from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AdminPowerLevelViewSet, PowerScaleView, PublicPowerLevelView

router = DefaultRouter()
router.register("admin/power-levels", AdminPowerLevelViewSet, basename="admin-power")

urlpatterns = [
    path("power-levels/scale/", PowerScaleView.as_view(), name="power-scale"),
    path("power-levels/", PublicPowerLevelView.as_view(), name="power-public"),
    *router.urls,
]
