"""Enable pg_trgm and add GIN trigram indexes for fast fuzzy search."""
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("cards", "0001_initial")]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name="card",
            index=GinIndex(
                name="card_name_trgm_idx",
                fields=["name"],
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="card",
            index=GinIndex(
                name="card_ability_trgm_idx",
                fields=["ability_text"],
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
