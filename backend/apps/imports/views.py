from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.permissions import IsPlatformAdmin

from .models import DataSource, ImportBatch
from .serializers import (
    DataSourceSerializer,
    ImportBatchSerializer,
    RawImportPayloadSerializer,
    TriggerImportSerializer,
)
from .services import ImportRunner
from .tasks import run_import_task


class DataSourceViewSet(viewsets.ModelViewSet):
    """Admin-only management of import data sources."""

    queryset = DataSource.objects.all().order_by("key")
    serializer_class = DataSourceSerializer
    permission_classes = [IsPlatformAdmin]
    lookup_field = "uuid"


class ImportBatchViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                         viewsets.GenericViewSet):
    """Admin-only monitoring of import batches (the sync admin screen backend)."""

    queryset = ImportBatch.objects.select_related("source").order_by("-created_at")
    serializer_class = ImportBatchSerializer
    permission_classes = [IsPlatformAdmin]
    lookup_field = "uuid"
    filterset_fields = ["kind", "status"]

    @extend_schema(request=TriggerImportSerializer, responses=ImportBatchSerializer)
    @action(detail=False, methods=["post"], url_path="trigger")
    def trigger(self, request):
        """Kick off an import (sync inline, or async via Celery)."""
        serializer = TriggerImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        source = DataSource.objects.filter(key=data["source_key"]).first()
        if not source:
            return Response(
                {"error": {"code": "not_found", "message": "Unknown data source."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if data.get("run_async"):
            task = run_import_task.delay(
                data["source_key"], data["kind"],
                data.get("set_external_id") or None, request.user.username,
            )
            return Response({"task_id": task.id, "status": "queued"},
                            status=status.HTTP_202_ACCEPTED)

        runner = ImportRunner(source, triggered_by=request.user.username)
        kind = data["kind"]
        if kind == "sets":
            batch = runner.import_sets()
        elif kind == "products":
            batch = runner.import_cards(data.get("set_external_id") or None)
        elif kind == "prices":
            batch = runner.import_prices()
        else:  # full
            batches = runner.full_sync(data.get("set_external_id") or None)
            return Response(ImportBatchSerializer(batches, many=True).data,
                            status=status.HTTP_201_CREATED)
        return Response(ImportBatchSerializer(batch).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="payloads")
    def payloads(self, request, uuid=None):
        batch = self.get_object()
        page = self.paginate_queryset(batch.payloads.all())
        serializer = RawImportPayloadSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)
