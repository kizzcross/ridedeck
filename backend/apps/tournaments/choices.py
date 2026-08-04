from django.db import models


class BracketType(models.TextChoices):
    SINGLE_ELIMINATION = "single_elimination", "Single elimination"
    DOUBLE_ELIMINATION = "double_elimination", "Double elimination"
    SWISS = "swiss", "Swiss"
    SWISS_TOP_CUT = "swiss_top_cut", "Swiss + Top Cut"
    ROUND_ROBIN = "round_robin", "Round robin"


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
