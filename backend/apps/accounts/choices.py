from django.db import models


class PlatformRole(models.TextChoices):
    """Global platform role. Tournament Organizer is NOT here — it is an
    object-level role scoped to a single tournament (see apps.tournaments)."""

    MEMBER = "member", "Member"
    PLATFORM_ADMIN = "platform_admin", "Platform Admin"


class Theme(models.TextChoices):
    DARK = "dark", "Dark"
    LIGHT = "light", "Light"
    SYSTEM = "system", "System"
