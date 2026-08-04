from django.db import models


class BanlistCategory(models.TextChoices):
    OFFICIAL = "official", "Official"
    COMMUNITY = "community", "Community"
    TOURNAMENT_CUSTOM = "tournament_custom", "Tournament custom"


class BanlistVersionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    SUPERSEDED = "superseded", "Superseded"


class RestrictionType(models.TextChoices):
    BANNED = "banned", "Banned"
    LIMIT_TO_1 = "limit_to_1", "Limit to 1"
    LIMIT_TO_2 = "limit_to_2", "Limit to 2"
    LIMIT_TO_N = "limit_to_n", "Limit to N"
    FIRST_VANGUARD_FORBIDDEN = "first_vanguard_forbidden", "First Vanguard forbidden"
    CHOICE_RESTRICTION = "choice_restriction", "Choice restriction"
    MAX_DISTINCT_FROM_GROUP = "max_distinct_from_group", "Max distinct from group"
    MAX_TOTAL_FROM_GROUP = "max_total_from_group", "Max total from group"
    DECK_DEPENDENT_RESTRICTION = "deck_dependent_restriction", "Deck-dependent restriction"
    ALLOWED_EXCEPTION = "allowed_exception", "Allowed exception"
    UNRESTRICTED_HISTORY = "unrestricted_history", "Unrestricted (history)"


class GroupKind(models.TextChoices):
    CHOICE = "choice", "Choice (pick one)"
    MAX_DISTINCT = "max_distinct", "Max distinct identities"
    MAX_TOTAL = "max_total", "Max total copies"


class ConditionType(models.TextChoices):
    NATION = "nation", "Nation"
    CLAN = "clan", "Clan"
    FORMAT = "format", "Format"
    HAS_CARD = "has_card", "Deck contains card"
    RIDELINE = "rideline", "Rideline"
