import secrets

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, UserPreference, UserProfile

_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no ambiguous chars


def generate_referral_code() -> str:
    while True:
        code = "".join(secrets.choice(_ALPHABET) for _ in range(8))
        if not UserProfile.objects.filter(referral_code=code).exists():
            return code


@receiver(post_save, sender=User)
def ensure_related_records(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(
            user=instance, defaults={"referral_code": generate_referral_code()}
        )
        UserPreference.objects.get_or_create(user=instance)
