from django.apps import apps
from rest_framework import serializers

from apps.accounts.serializers import MiniUserSerializer

from .models import Comment

# target_type -> (app_label.ModelName, whether it has a soft-delete flag)
_TARGET_MODELS = {
    Comment.Target.DECK: ("decks.Deck", True),
    Comment.Target.BANLIST: ("banlists.Banlist", True),
    Comment.Target.CARD: ("cards.Card", False),
    Comment.Target.TOURNAMENT: ("tournaments.Tournament", True),
    Comment.Target.PROFILE: ("accounts.User", False),
}


def target_exists(target_type: str, target_uuid) -> bool:
    spec = _TARGET_MODELS.get(target_type)
    if not spec:
        return False
    label, soft = spec
    model = apps.get_model(label)
    qs = model.objects.filter(uuid=target_uuid)
    if soft:
        qs = qs.filter(deleted_at__isnull=True)
    return qs.exists()


class CommentSerializer(serializers.ModelSerializer):
    author = MiniUserSerializer(read_only=True)
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["uuid", "target_type", "target_uuid", "author", "body",
                  "can_delete", "created_at"]
        read_only_fields = ["uuid", "author", "created_at"]

    def validate(self, attrs):
        tt, tu = attrs.get("target_type"), attrs.get("target_uuid")
        if not target_exists(tt, tu):
            raise serializers.ValidationError("Alvo do comentário não encontrado.")
        return attrs

    def get_can_delete(self, obj) -> bool:
        user = self.context["request"].user
        return user.is_authenticated and (
            obj.author_id == user.id or user.is_platform_admin
        )
