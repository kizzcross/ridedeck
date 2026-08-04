from django.db import models


class Zone(models.TextChoices):
    MAIN_DECK = "main_deck", "Main Deck"
    RIDE_DECK = "ride_deck", "Ride Deck"
    G_DECK = "g_deck", "G Deck"


class Visibility(models.TextChoices):
    PRIVATE = "private", "Private"
    UNLISTED = "unlisted", "Unlisted"
    PUBLIC = "public", "Public"
