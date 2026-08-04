from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.cards.serializers import CardListSerializer

from .models import FavoriteCard, Friendship, UserPreference, UserProfile
from .services import apply_referral

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Self view — includes the private referral code."""

    class Meta:
        model = UserProfile
        fields = ["display_name", "bio", "avatar", "avatar_key", "country",
                  "favorite_nation", "referral_code"]
        read_only_fields = ["avatar", "referral_code"]


class PublicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ["display_name", "bio", "avatar", "avatar_key", "country", "favorite_nation"]


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = ["theme", "default_format", "show_collection_in_builder", "locale"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    preference = UserPreferenceSerializer(read_only=True)
    is_platform_admin = serializers.BooleanField(read_only=True)
    friend_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["uuid", "email", "username", "role", "is_platform_admin",
                  "email_verified", "date_joined", "profile", "preference", "friend_count"]
        read_only_fields = ["uuid", "role", "is_platform_admin", "email_verified", "date_joined"]

    def get_friend_count(self, obj) -> int:
        return len(Friendship.friend_ids(obj))


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["email", "username", "password", "password_confirm", "referral_code"]

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is taken.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        referral_code = validated_data.pop("referral_code", "")
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        if referral_code:
            apply_referral(user, referral_code.strip())
        return user


# --- Social -------------------------------------------------------------
class MiniUserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source="profile.display_name", read_only=True)
    avatar_key = serializers.CharField(source="profile.avatar_key", read_only=True)
    favorite_nation = serializers.CharField(source="profile.favorite_nation", read_only=True)
    is_platform_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ["uuid", "username", "display_name", "avatar_key", "favorite_nation",
                  "role", "is_platform_admin"]


class FriendshipSerializer(serializers.ModelSerializer):
    requester = MiniUserSerializer(read_only=True)
    addressee = MiniUserSerializer(read_only=True)
    direction = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ["uuid", "requester", "addressee", "status", "direction",
                  "created_at", "responded_at"]

    def get_direction(self, obj) -> str:
        me = self.context["request"].user
        if obj.status == Friendship.Status.ACCEPTED:
            return "friend"
        return "outgoing" if obj.requester_id == me.id else "incoming"


class PublicUserSerializer(serializers.ModelSerializer):
    profile = PublicProfileSerializer(read_only=True)
    friend_count = serializers.SerializerMethodField()
    friendship_state = serializers.SerializerMethodField()
    friendship_uuid = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["uuid", "username", "role", "date_joined", "profile",
                  "friend_count", "friendship_state", "friendship_uuid"]

    def get_friend_count(self, obj) -> int:
        return len(Friendship.friend_ids(obj))

    def _friendship(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated or request.user.id == obj.id:
            return None
        me = request.user
        return (
            Friendship.objects.filter(requester__in=[me, obj], addressee__in=[me, obj]).first()
        )

    def get_friendship_state(self, obj) -> str:
        request = self.context.get("request")
        if request and request.user.is_authenticated and request.user.id == obj.id:
            return "self"
        f = self._friendship(obj)
        if not f:
            return "none"
        if f.status == Friendship.Status.ACCEPTED:
            return "friend"
        return "outgoing" if f.requester_id == request.user.id else "incoming"

    def get_friendship_uuid(self, obj) -> str | None:
        f = self._friendship(obj)
        return str(f.uuid) if f else None


class FavoriteCardSerializer(serializers.ModelSerializer):
    card = CardListSerializer(read_only=True)

    class Meta:
        model = FavoriteCard
        fields = ["uuid", "card", "created_at"]
