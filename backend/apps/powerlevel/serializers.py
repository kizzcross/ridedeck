from rest_framework import serializers

from .models import (
    CardPowerLevel,
    CardPowerLevelHistory,
    PowerLevelScale,
    TournamentPowerPolicy,
)


class PowerLevelScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PowerLevelScale
        fields = ["uuid", "name", "min_value", "max_value", "descriptions"]


class CardPowerLevelSerializer(serializers.ModelSerializer):
    card_uuid = serializers.UUIDField(source="card.uuid", read_only=True)
    card_name = serializers.CharField(source="card.name", read_only=True)
    updated_by = serializers.CharField(source="updated_by.username", read_only=True)

    class Meta:
        model = CardPowerLevel
        fields = ["uuid", "card_uuid", "card_name", "format_code", "value", "status",
                  "justification", "confidence", "tags", "version", "updated_by", "updated_at"]


class PowerHistorySerializer(serializers.ModelSerializer):
    admin = serializers.CharField(source="admin.username", read_only=True)

    class Meta:
        model = CardPowerLevelHistory
        fields = ["previous_value", "new_value", "admin", "justification", "source",
                  "version", "created_at"]


class SetPowerLevelSerializer(serializers.Serializer):
    card = serializers.UUIDField()
    format_code = serializers.CharField()
    value = serializers.IntegerField(min_value=1, max_value=10)
    justification = serializers.CharField()  # required — spec-mandated
    status = serializers.ChoiceField(choices=["draft", "published"], default="published")
    confidence = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False)


class BulkSetPowerLevelSerializer(serializers.Serializer):
    cards = serializers.ListField(child=serializers.UUIDField(), min_length=1)
    format_code = serializers.CharField()
    value = serializers.IntegerField(min_value=1, max_value=10)
    justification = serializers.CharField()


class TournamentPowerPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentPowerPolicy
        fields = ["uuid", "name", "kind", "config"]
