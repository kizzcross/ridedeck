from rest_framework import serializers

from .models import (
    FormatConstructionRule,
    FormatRuleVersion,
    FormatTriggerRule,
    FormatZoneRule,
    GameFormat,
)


class ZoneRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormatZoneRule
        fields = ["zone", "min_count", "max_count"]


class TriggerRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormatTriggerRule
        fields = ["total_triggers", "per_type_limits", "over_trigger_limit", "counted_zones"]


class ConstructionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormatConstructionRule
        fields = ["copies_per_identity", "nation_locked", "clan_locked",
                  "requires_first_vanguard", "extra"]


class RuleVersionSerializer(serializers.ModelSerializer):
    zone_rules = ZoneRuleSerializer(many=True, read_only=True)
    trigger_rule = TriggerRuleSerializer(read_only=True)
    construction_rule = ConstructionRuleSerializer(read_only=True)

    class Meta:
        model = FormatRuleVersion
        fields = ["version", "valid_from", "valid_until", "notes", "source",
                  "zone_rules", "trigger_rule", "construction_rule"]


class GameFormatSerializer(serializers.ModelSerializer):
    current_rules = serializers.SerializerMethodField()

    class Meta:
        model = GameFormat
        fields = ["uuid", "code", "name", "description", "is_official", "current_rules"]

    def get_current_rules(self, obj):
        rv = obj.current_version()
        return RuleVersionSerializer(rv).data if rv else None
