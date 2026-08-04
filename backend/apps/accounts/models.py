import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel, TimeStampedModel

from .choices import PlatformRole, Theme
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user: email login + public username handle + global platform role."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=32, unique=True)
    role = models.CharField(
        max_length=24, choices=PlatformRole.choices, default=PlatformRole.MEMBER, db_index=True
    )

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    email_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        indexes = [models.Index(fields=["role"])]

    def __str__(self) -> str:
        return f"{self.username} <{self.email}>"

    @property
    def is_platform_admin(self) -> bool:
        """Single source of truth for admin authority. Superusers count too."""
        return self.is_superuser or self.role == PlatformRole.PLATFORM_ADMIN

    def promote_to_platform_admin(self):
        self.role = PlatformRole.PLATFORM_ADMIN
        self.is_staff = True
        self.save(update_fields=["role", "is_staff"])


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=64, blank=True)
    bio = models.TextField(blank=True, max_length=1000)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    country = models.CharField(max_length=2, blank=True)
    favorite_nation = models.CharField(max_length=64, blank=True)
    referral_code = models.CharField(max_length=16, blank=True, unique=True, null=True,
                                     db_index=True)
    # Preset avatar chosen from the pixel nation logos, e.g. "nation:dragon_empire".
    # An uploaded image (avatar) takes precedence when present.
    avatar_key = models.CharField(max_length=64, blank=True)
    referred_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="referrals"
    )

    def __str__(self) -> str:
        return f"Profile<{self.user.username}>"


class UserPreference(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preference")
    theme = models.CharField(max_length=8, choices=Theme.choices, default=Theme.DARK)
    default_format = models.CharField(max_length=32, blank=True)
    show_collection_in_builder = models.BooleanField(default=True)
    locale = models.CharField(max_length=8, default="en")

    def __str__(self) -> str:
        return f"Preference<{self.user.username}>"


class Friendship(BaseModel):
    """A friendship or a pending request between two users.

    Direction matters only while pending (requester → addressee). Once accepted
    it is symmetric: use ``Friendship.friends_of(user)`` for the friend list.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"

    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friendships_initiated"
    )
    addressee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="friendships_received"
    )
    status = models.CharField(max_length=12, choices=Status.choices,
                              default=Status.PENDING, db_index=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["requester", "addressee"],
                                    name="uniq_friendship_pair"),
            models.CheckConstraint(condition=~models.Q(requester=models.F("addressee")),
                                   name="no_self_friendship"),
        ]
        indexes = [models.Index(fields=["addressee", "status"])]

    def __str__(self) -> str:
        return f"{self.requester_id}→{self.addressee_id} [{self.status}]"

    @staticmethod
    def friend_ids(user) -> set[int]:
        qs = Friendship.objects.filter(status=Friendship.Status.ACCEPTED).filter(
            models.Q(requester=user) | models.Q(addressee=user)
        ).values_list("requester_id", "addressee_id")
        ids: set[int] = set()
        for req_id, addr_id in qs:
            ids.add(addr_id if req_id == user.id else req_id)
        return ids

    @staticmethod
    def friends_of(user):
        return User.objects.filter(id__in=Friendship.friend_ids(user))


class FavoriteCard(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_cards")
    card = models.ForeignKey("cards.Card", on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "card"], name="uniq_favorite_card")
        ]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self) -> str:
        return f"{self.user_id} ♥ {self.card_id}"
