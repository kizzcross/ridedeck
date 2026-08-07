from django.db import models


class BracketType(models.TextChoices):
    SINGLE_ELIMINATION = "single_elimination", "Single elimination"
    DOUBLE_ELIMINATION = "double_elimination", "Double elimination"
    SWISS = "swiss", "Swiss"
    SWISS_TOP_CUT = "swiss_top_cut", "Swiss + Top Cut"
    ROUND_ROBIN = "round_robin", "Round robin"


# --- Roster championship mode -------------------------------------------------
class TournamentKind(models.TextChoices):
    STANDARD = "standard", "Standard (single deck)"
    ROSTER = "roster", "Roster championship"


class FormatKind(models.TextChoices):
    POINTS = "points", "Points only"
    BRACKET = "bracket", "Bracket only"
    HYBRID = "hybrid", "Hybrid (points → bracket)"


class SeedSource(models.TextChoices):
    RANDOM = "random", "Random"
    MANUAL = "manual", "Manual"
    PLATFORM_RANKING = "platform_ranking", "Platform ranking"


class DeckSelectionMode(models.TextChoices):
    MANUAL = "manual", "Manual secret pick"
    RANDOM_FREE = "random_free", "Random — free repeats"
    RANDOM_NO_CONSECUTIVE = "random_no_consecutive", "Random — no consecutive repeat"
    RANDOM_ROTATION = "random_rotation", "Random — rotation (all before repeat)"
    PREDETERMINED_ORDER = "predetermined_order", "Predetermined random order"
    CHOOSE_FROM_RANDOM = "choose_from_random", "Choose from N random"


class DrawTiming(models.TextChoices):
    BEFORE_PAIRING = "before_pairing", "Before pairing"
    AFTER_PAIRING = "after_pairing", "After pairing"
    AUTO_ROUND_START = "auto_round_start", "Auto at round start"
    MANUAL_OWNER = "manual_owner", "Manual by owner"


class SequenceSelfVisibility(models.TextChoices):
    FROM_START = "from_start", "Visible from start"
    EACH_ROUND = "each_round", "Revealed each round"


class SequenceOpponentVisibility(models.TextChoices):
    PUBLIC = "public", "Public"
    HIDDEN = "hidden", "Hidden from opponents"


class RosterVisibility(models.TextChoices):
    OPEN = "open", "Open"
    PARTIAL = "partial", "Partially open"
    CLOSED = "closed", "Closed"


class AceRule(models.TextChoices):
    MANUAL_ONCE = "manual_once", "Player uses Ace once"
    REPLACE_DRAW = "replace_draw", "Ace replaces a draw once"
    WEIGHTED_RANDOM = "weighted_random", "Ace weighted in random"
    EXTRA_IN_ROTATION = "extra_in_rotation", "Ace appears extra in rotation"
    TIEBREAK_WINS = "tiebreak_wins", "Ace wins as tiebreak"
    VISUAL_ONLY = "visual_only", "Visual only"


class AceReveal(models.TextChoices):
    PUBLIC = "public", "Public"
    HIDDEN_UNTIL_FIRST_USE = "hidden_until_first_use", "Hidden until first use"


class RosterStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    VALID = "valid", "Valid"
    INVALID = "invalid", "Invalid"
    CONFIRMED = "confirmed", "Confirmed"
    LOCKED = "locked", "Locked"


class SelectionMethod(models.TextChoices):
    MANUAL = "manual", "Manual"
    RANDOM = "random", "Random"
    PREDETERMINED = "predetermined", "Predetermined"
    CHOOSE_FROM_RANDOM = "choose_from_random", "Choose from random"


class AceEventKind(models.TextChoices):
    USED = "used", "Used"
    REPLACED_DRAW = "replaced_draw", "Replaced a draw"
    REVEALED = "revealed", "Revealed"


class PenaltyKind(models.TextChoices):
    WARNING = "warning", "Warning"
    GAME_LOSS = "game_loss", "Game loss"
    MATCH_LOSS = "match_loss", "Match loss"
    POINTS_DEDUCTION = "points_deduction", "Points deduction"
    DISQUALIFICATION = "disqualification", "Disqualification"


class TournamentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    REGISTRATION = "registration", "Registration open"
    LOCKED = "locked", "Registration locked"
    CHECK_IN = "check_in", "Check-in"
    RUNNING = "running", "Running"
    FINISHED = "finished", "Finished"
    CANCELLED = "cancelled", "Cancelled"


class Visibility(models.TextChoices):
    PUBLIC = "public", "Public"
    UNLISTED = "unlisted", "Unlisted"
    PRIVATE = "private", "Private"


class RegistrationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"


class ParticipantStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CHECKED_IN = "checked_in", "Checked in"
    DROPPED = "dropped", "Dropped"
    DISQUALIFIED = "disqualified", "Disqualified"


class DecklistVisibility(models.TextChoices):
    OPEN = "open", "Open during registration"
    HIDDEN_UNTIL_START = "hidden_until_start", "Hidden until start"
    HIDDEN_UNTIL_TOP_CUT = "hidden_until_top_cut", "Hidden until Top Cut"
    AFTER_END = "after_end", "Public only after the end"
    ALWAYS_PRIVATE = "always_private", "Always private"


class StaffRole(models.TextChoices):
    CO_ORGANIZER = "co_organizer", "Co-organizer"
    JUDGE = "judge", "Judge"


class MatchState(models.TextChoices):
    PENDING = "pending", "Pending"       # waiting to be played
    REPORTED = "reported", "Reported"    # one side reported, awaiting confirm
    DISPUTED = "disputed", "Disputed"
    BYE = "bye", "Bye"
    DONE = "done", "Done"                # confirmed / resolved, winner set


class RoundStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
