from rest_framework import serializers

from .models import DataSource, ImportBatch, RawImportPayload


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ["uuid", "key", "name", "base_url", "is_enabled",
                  "rate_limit_per_sec", "config"]
        read_only_fields = ["uuid"]


class ImportBatchSerializer(serializers.ModelSerializer):
    source_key = serializers.CharField(source="source.key", read_only=True)
    metrics = serializers.DictField(read_only=True)

    class Meta:
        model = ImportBatch
        fields = ["uuid", "source_key", "kind", "status", "is_incremental",
                  "started_at", "finished_at", "processed", "created", "updated",
                  "skipped", "failed", "metrics", "error", "triggered_by", "created_at"]
        read_only_fields = fields


class RawImportPayloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawImportPayload
        fields = ["id", "endpoint", "external_id", "payload", "received_at"]


class TriggerImportSerializer(serializers.Serializer):
    source_key = serializers.CharField()
    kind = serializers.ChoiceField(choices=["sets", "products", "prices", "full"])
    set_external_id = serializers.CharField(required=False, allow_blank=True)
    run_async = serializers.BooleanField(default=False)
