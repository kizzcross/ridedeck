"""Friend-request and referral logic (kept out of views/serializers)."""
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Friendship, User, UserProfile


def apply_referral(new_user: User, referral_code: str) -> User | None:
    """Link ``new_user`` to the referrer and make them friends immediately.

    Returns the referrer, or None if the code is invalid / self-referral.
    """
    if not referral_code:
        return None
    profile = (
        UserProfile.objects.filter(referral_code=referral_code)
        .select_related("user")
        .first()
    )
    if not profile or profile.user_id == new_user.id:
        return None
    referrer = profile.user

    new_user.profile.referred_by = referrer
    new_user.profile.save(update_fields=["referred_by"])

    # Auto-friend: someone who joins via the link is already a friend.
    Friendship.objects.get_or_create(
        requester=referrer,
        addressee=new_user,
        defaults={"status": Friendship.Status.ACCEPTED, "responded_at": timezone.now()},
    )
    return referrer


@transaction.atomic
def send_friend_request(from_user: User, to_user: User) -> Friendship:
    if from_user.id == to_user.id:
        raise ValidationError("You cannot add yourself.")

    # Already friends or a request already exists in either direction?
    existing = Friendship.objects.filter(
        requester__in=[from_user, to_user], addressee__in=[from_user, to_user]
    ).first()
    if existing:
        if existing.status == Friendship.Status.ACCEPTED:
            raise ValidationError("You are already friends.")
        # A pending request from the other side → accept it (mutual add).
        if existing.requester_id == to_user.id:
            return accept_friend_request(existing, from_user)
        raise ValidationError("Friend request already sent.")

    try:
        return Friendship.objects.create(requester=from_user, addressee=to_user)
    except IntegrityError as exc:  # pragma: no cover - race
        raise ValidationError("Friend request already exists.") from exc


def accept_friend_request(friendship: Friendship, user: User) -> Friendship:
    if friendship.addressee_id != user.id:
        raise ValidationError("Only the recipient can accept this request.")
    if friendship.status == Friendship.Status.ACCEPTED:
        return friendship
    friendship.status = Friendship.Status.ACCEPTED
    friendship.responded_at = timezone.now()
    friendship.save(update_fields=["status", "responded_at"])
    return friendship


def remove_or_reject(friendship: Friendship, user: User) -> None:
    """Reject a pending request, cancel one you sent, or unfriend."""
    if user.id not in (friendship.requester_id, friendship.addressee_id):
        raise ValidationError("Not your friendship.")
    friendship.delete()
