from rest_framework import serializers

from .models import (
    Card,
    CardExternalIdentifier,
    CardFormatLegality,
    CardPrinting,
    CardSet,
)


class CardSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardSet
        fields = ["uuid", "code", "name", "slug", "release_date", "card_count"]


class CardPrintingSerializer(serializers.ModelSerializer):
    set_code = serializers.CharField(source="card_set.code", read_only=True)
    set_name = serializers.CharField(source="card_set.name", read_only=True)

    class Meta:
        model = CardPrinting
        fields = ["uuid", "card_number", "set_code", "set_name", "rarity", "language",
                  "illustrator", "finish", "image_url", "price", "release_date"]


class CardFormatLegalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CardFormatLegality
        fields = ["format_code", "legality"]


class CardExternalIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardExternalIdentifier
        fields = ["source", "identifier"]


class CardListSerializer(serializers.ModelSerializer):
    """Compact representation for catalog grids."""

    default_printing = serializers.SerializerMethodField()

    class Meta:
        model = Card
        fields = ["uuid", "name", "slug", "grade", "power", "shield", "critical",
                  "card_type", "trigger", "nation", "clan", "is_persona_ride",
                  "default_printing"]

    def get_default_printing(self, obj) -> dict | None:
        printings = getattr(obj, "prefetched_printings", None)
        printing = printings[0] if printings else obj.printings.first()
        if not printing:
            return None
        return {
            "uuid": str(printing.uuid),
            "card_number": printing.card_number,
            "rarity": printing.rarity,
            "image_url": printing.image_url,
            "price": str(printing.price) if printing.price is not None else None,
        }


class CardDetailSerializer(serializers.ModelSerializer):
    printings = CardPrintingSerializer(many=True, read_only=True)
    format_legalities = CardFormatLegalitySerializer(many=True, read_only=True)
    external_ids = CardExternalIdentifierSerializer(many=True, read_only=True)
    default_printing = serializers.SerializerMethodField()

    def get_default_printing(self, obj) -> dict | None:
        # Prefer a printing that actually has artwork so the detail view shows
        # the real card image rather than the placeholder face.
        printing = obj.printings.exclude(image_url="").first() or obj.printings.first()
        if not printing:
            return None
        return {
            "uuid": str(printing.uuid),
            "card_number": printing.card_number,
            "rarity": printing.rarity,
            "image_url": printing.image_url,
            "price": str(printing.price) if printing.price is not None else None,
        }

    class Meta:
        model = Card
        fields = ["uuid", "name", "slug", "ability_text", "flavor_text", "grade",
                  "power", "shield", "critical", "card_type", "trigger", "nation",
                  "clan", "race", "is_persona_ride", "keywords", "rules_data",
                  "equivalence_strategy", "default_printing", "printings",
                  "format_legalities", "external_ids"]
