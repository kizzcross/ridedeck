from rest_framework import serializers

from .models import (
    Banlist,
    BanlistComment,
    BanlistEntry,
    BanlistVersion,
    RestrictionGroup,
    RestrictionGroupMember,
)


class MiniCardSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    name = serializers.CharField()
    grade = serializers.IntegerField()
    nation = serializers.CharField()
    clan = serializers.CharField()
    image = serializers.SerializerMethodField()

    def get_image(self, obj) -> str:
        p = obj.printings.first()
        return p.image_url if p else ""


class GroupMemberSerializer(serializers.ModelSerializer):
    card = MiniCardSerializer(read_only=True)

    class Meta:
        model = RestrictionGroupMember
        fields = ["uuid", "card", "per_card_limit"]


class RestrictionGroupSerializer(serializers.ModelSerializer):
    members = GroupMemberSerializer(many=True, read_only=True)

    class Meta:
        model = RestrictionGroup
        fields = ["uuid", "name", "kind", "limit_value", "note", "members"]


class BanlistEntrySerializer(serializers.ModelSerializer):
    card = MiniCardSerializer(read_only=True)
    group = RestrictionGroupSerializer(read_only=True)
    effective_limit = serializers.SerializerMethodField()

    class Meta:
        model = BanlistEntry
        fields = ["uuid", "restriction_type", "card", "group", "limit_value",
                  "effective_limit", "note"]

    def get_effective_limit(self, obj) -> int:
        return obj.effective_limit()


class BanlistVersionSerializer(serializers.ModelSerializer):
    entries = BanlistEntrySerializer(many=True, read_only=True)

    class Meta:
        model = BanlistVersion
        fields = ["uuid", "version", "status", "effective_date", "notes", "source", "entries"]


class OwnerMiniSerializer(serializers.Serializer):
    username = serializers.CharField()
    uuid = serializers.UUIDField()


class BanlistListSerializer(serializers.ModelSerializer):
    owner = OwnerMiniSerializer(read_only=True)
    is_official = serializers.BooleanField(read_only=True)
    entry_count = serializers.SerializerMethodField()

    class Meta:
        model = Banlist
        fields = ["uuid", "name", "category", "is_official", "format_code", "objective",
                  "owner", "like_count", "favorite_count", "entry_count", "updated_at"]

    def get_entry_count(self, obj) -> int:
        return obj.current_version.entries.count() if obj.current_version_id else 0


class BanlistDetailSerializer(serializers.ModelSerializer):
    owner = OwnerMiniSerializer(read_only=True)
    is_official = serializers.BooleanField(read_only=True)
    current_version = BanlistVersionSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Banlist
        fields = ["uuid", "name", "description", "objective", "category", "is_official",
                  "format_code", "owner", "source", "is_public", "is_listed", "forked_from",
                  "like_count", "favorite_count", "current_version", "is_owner",
                  "created_at", "updated_at"]

    def get_is_owner(self, obj) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.owner_id == request.user.id)


class BanlistWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banlist
        fields = ["name", "description", "objective", "format_code", "is_public", "is_listed"]


class EntryWriteSerializer(serializers.Serializer):
    restriction_type = serializers.CharField()
    card = serializers.UUIDField(required=False, allow_null=True)
    group = serializers.UUIDField(required=False, allow_null=True)
    limit_value = serializers.IntegerField(required=False, allow_null=True)
    note = serializers.CharField(required=False, allow_blank=True)


class GroupWriteSerializer(serializers.Serializer):
    name = serializers.CharField()
    kind = serializers.ChoiceField(choices=["choice", "max_distinct", "max_total"])
    limit_value = serializers.IntegerField(default=1)
    members = serializers.ListField(child=serializers.UUIDField(), default=list)


class BanlistCommentSerializer(serializers.ModelSerializer):
    author = OwnerMiniSerializer(read_only=True)

    class Meta:
        model = BanlistComment
        fields = ["uuid", "author", "body", "created_at"]
        read_only_fields = ["author", "created_at"]
