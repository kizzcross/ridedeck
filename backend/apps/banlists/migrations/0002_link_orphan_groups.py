"""Back-link restriction groups that were created without a BanlistEntry.

The group action used to create the RestrictionGroup but not the entry that
points at it, so those groups never surfaced in the version. This attaches a
choice/max entry to any orphaned group.
"""
from django.db import migrations

_KIND_TO_RESTRICTION = {
    "choice": "choice_restriction",
    "max_distinct": "max_distinct_from_group",
    "max_total": "max_total_from_group",
}


def link_orphans(apps, schema_editor):
    RestrictionGroup = apps.get_model("banlists", "RestrictionGroup")
    BanlistEntry = apps.get_model("banlists", "BanlistEntry")
    for group in RestrictionGroup.objects.filter(entries__isnull=True):
        BanlistEntry.objects.create(
            version=group.version,
            group=group,
            restriction_type=_KIND_TO_RESTRICTION.get(group.kind, "choice_restriction"),
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("banlists", "0001_initial")]
    operations = [migrations.RunPython(link_orphans, noop)]
