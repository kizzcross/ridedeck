from rest_framework import serializers

from apps.cards.serializers import CardListSerializer

from .models import Deck, DeckComment, DeckEntry, DeckVersion


class DeckEntrySerializer(serializers.ModelSerializer):
    card = CardListSerializer(read_only=True)
    preferred_printing = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = DeckEntry
        fields = ["uuid", "card", "zone", "quantity", "preferred_printing"]


class DeckVersionSerializer(serializers.ModelSerializer):
    entries = DeckEntrySerializer(many=True, read_only=True)
    zone_counts = serializers.SerializerMethodField()

    class Meta:
        model = DeckVersion
        fields = ["uuid", "version_number", "notes", "entries", "zone_counts"]

    def get_zone_counts(self, obj) -> dict:
        return obj.zone_counts()


class OwnerSerializer(serializers.Serializer):
    username = serializers.CharField()
    uuid = serializers.UUIDField()
    avatar_key = serializers.SerializerMethodField()

    def get_avatar_key(self, obj) -> str:
        return getattr(getattr(obj, "profile", None), "avatar_key", "")


class DeckListSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer(read_only=True)
    cover_image = serializers.SerializerMethodField()
    main_count = serializers.SerializerMethodField()

    class Meta:
        model = Deck
        fields = ["uuid", "title", "format_code", "visibility", "owner", "nation_focus",
                  "clan_focus", "archetype", "like_count", "favorite_count",
                  "cover_image", "main_count", "updated_at"]

    def get_cover_image(self, obj) -> str | None:
        return obj.cover_printing.image_url if obj.cover_printing else None

    def get_main_count(self, obj) -> int:
        if obj.current_version_id:
            return obj.current_version.zone_counts().get("main_deck", 0)
        return 0


class DeckDetailSerializer(serializers.ModelSerializer):
    owner = OwnerSerializer(read_only=True)
    current_version = DeckVersionSerializer(read_only=True)
    is_owner = serializers.SerializerMethodField()
    tags = serializers.SlugRelatedField(slug_field="name", many=True, read_only=True)

    class Meta:
        model = Deck
        fields = ["uuid", "title", "description", "format_code", "visibility", "owner",
                  "nation_focus", "clan_focus", "archetype", "tags", "guide", "combos",
                  "matchups", "side_notes", "changelog", "like_count", "favorite_count",
                  "forked_from", "current_version", "is_owner", "created_at", "updated_at"]
        read_only_fields = ["like_count", "favorite_count", "forked_from"]

    def get_is_owner(self, obj) -> bool:
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.owner_id == request.user.id)


class DeckWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deck
        fields = ["title", "description", "format_code", "visibility", "nation_focus",
                  "clan_focus", "archetype", "guide", "combos", "matchups", "side_notes",
                  "changelog"]


class SetEntrySerializer(serializers.Serializer):
    card = serializers.UUIDField()
    zone = serializers.ChoiceField(choices=["main_deck", "ride_deck", "g_deck"])
    quantity = serializers.IntegerField(min_value=0, max_value=99)
    preferred_printing = serializers.UUIDField(required=False, allow_null=True)


class DeckCommentSerializer(serializers.ModelSerializer):
    author = OwnerSerializer(read_only=True)

    class Meta:
        model = DeckComment
        fields = ["uuid", "author", "body", "created_at"]
        read_only_fields = ["author", "created_at"]
