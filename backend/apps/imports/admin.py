from django.contrib import admin

from .models import DataSource, ImportBatch, RawImportPayload


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "is_enabled", "rate_limit_per_sec")
    search_fields = ("key", "name")


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = ("kind", "status", "source", "processed", "created", "updated",
                    "failed", "created_at")
    list_filter = ("kind", "status", "source")
    readonly_fields = ("metrics",)


@admin.register(RawImportPayload)
class RawImportPayloadAdmin(admin.ModelAdmin):
    list_display = ("external_id", "endpoint", "batch", "received_at")
    search_fields = ("external_id",)
