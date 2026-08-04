from django.db import models


class Grade(models.IntegerChoices):
    G0 = 0, "Grade 0"
    G1 = 1, "Grade 1"
    G2 = 2, "Grade 2"
    G3 = 3, "Grade 3"
    G4 = 4, "Grade 4"


class CardType(models.TextChoices):
    NORMAL_UNIT = "normal_unit", "Normal Unit"
    TRIGGER_UNIT = "trigger_unit", "Trigger Unit"
    G_UNIT = "g_unit", "G Unit"
    ORDER = "order", "Order"
    SET_ORDER = "set_order", "Set Order"
    BLITZ_ORDER = "blitz_order", "Blitz Order"
    TOKEN = "token", "Token"


class TriggerType(models.TextChoices):
    NONE = "", "—"
    CRITICAL = "critical", "Critical"
    DRAW = "draw", "Draw"
    FRONT = "front", "Front"
    HEAL = "heal", "Heal"
    STAND = "stand", "Stand"
    OVER = "over", "Over"


class Nation(models.TextChoices):
    """Cardfight!! Vanguard nations across eras. Original/G-era nations group the
    classic clans; D-era nations replaced clans. Card.clan holds the clan
    (G-era) free-form."""

    NONE = "", "—"
    # D-era (overDress) nations
    DRAGON_EMPIRE = "dragon_empire", "Dragon Empire"
    DARK_STATES = "dark_states", "Dark States"
    BRANDT_GATE = "brandt_gate", "Brandt Gate"
    KETER_SANCTUARY = "keter_sanctuary", "Keter Sanctuary"
    STOICHEIA = "stoicheia", "Stoicheia"
    LYRICAL_MONASTERIO = "lyrical_monasterio", "Lyrical Monasterio"
    # Original / G-era nations
    UNITED_SANCTUARY = "united_sanctuary", "United Sanctuary"
    DARK_ZONE = "dark_zone", "Dark Zone"
    MAGALLANICA = "magallanica", "Magallanica"
    ZOO = "zoo", "Zoo"
    STAR_GATE = "star_gate", "Star Gate"


class Legality(models.TextChoices):
    LEGAL = "legal", "Legal"
    NOT_LEGAL = "not_legal", "Not legal"
    RESTRICTED = "restricted", "Restricted"


class EquivalenceStrategy(models.TextChoices):
    """How two printings/cards are considered the same identity for copy limits,
    banlist and power level."""

    CANONICAL_IDENTITY = "canonical_identity", "Canonical identity (default)"
    NORMALIZED_NAME = "normalized_name", "Normalized name"
    ABILITY_EQUIVALENT = "ability_equivalent", "Equivalent ability text"
    OFFICIAL_IDENTIFIER = "official_identifier", "Official identifier"
    ADMIN_GROUP = "admin_group", "Admin-registered equivalence group"
