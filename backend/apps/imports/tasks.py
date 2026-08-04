from celery import shared_task

from .models import DataSource
from .services import ImportRunner


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def run_import_task(self, source_key: str, kind: str, set_external_id: str | None = None,
                    triggered_by: str = "system"):
    source = DataSource.objects.get(key=source_key)
    runner = ImportRunner(source, triggered_by=triggered_by)
    if kind == "sets":
        batch = runner.import_sets()
    elif kind == "products":
        batch = runner.import_cards(set_external_id)
    elif kind == "prices":
        batch = runner.import_prices()
    elif kind == "full":
        batches = runner.full_sync(set_external_id)
        return [str(b.uuid) for b in batches]
    else:
        raise ValueError(f"Unknown import kind '{kind}'")
    return str(batch.uuid)
