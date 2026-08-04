from rest_framework.routers import DefaultRouter

from .views import DataSourceViewSet, ImportBatchViewSet

router = DefaultRouter()
router.register("admin/data-sources", DataSourceViewSet, basename="data-source")
router.register("admin/imports", ImportBatchViewSet, basename="import-batch")

urlpatterns = router.urls
