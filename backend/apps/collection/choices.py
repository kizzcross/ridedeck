from django.db import models


class Condition(models.TextChoices):
    MINT = "mint", "Mint"
    NEAR_MINT = "near_mint", "Near Mint"
    LIGHTLY_PLAYED = "lightly_played", "Lightly Played"
    MODERATELY_PLAYED = "moderately_played", "Moderately Played"
    HEAVILY_PLAYED = "heavily_played", "Heavily Played"
    DAMAGED = "damaged", "Damaged"


class WishlistPriority(models.IntegerChoices):
    LOW = 1, "Low"
    MEDIUM = 2, "Medium"
    HIGH = 3, "High"
