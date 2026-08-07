"""Tournaments.

Any authenticated user can create a tournament and becomes its Tournament
Organizer (an object-level role — NOT a global one). Rules, banlist, power policy
and each submitted decklist are frozen as immutable snapshots when registration
locks, so later changes to global data never alter an in-progress tournament.
"""
from django.conf import settings
from django.db import models

from apps.common.models import BaseModel, SoftDeleteModel

from .choices import (
    AceEventKind,
    AceReveal,
    AceRule,
    BracketType,
    DecklistVisibility,
    DeckSelectionMode,
    DrawTiming,
    FormatKind,
    MatchState,
    ParticipantStatus,
    PenaltyKind,
    RegistrationStatus,
    RosterStatus,
    RosterVisibility,
    RoundStatus,
    SeedSource,
    SelectionMethod,
    SequenceOpponentVisibility,
    SequenceSelfVisibility,
    StaffRole,
    TournamentKind,
    TournamentStatus,
    Visibility,
)


class Tournament(BaseModel, SoftDeleteModel):
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    image = models.URLField(blank=True, max_length=500)
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  related_name="tournaments_organized")

    format_code = models.CharField(max_length=32, default="standard")
    banlist = models.ForeignKey("banlists.Banlist", on_delete=models.SET_NULL, null=True,
                                blank=True, related_name="tournaments")
    banlist_version_number = models.PositiveIntegerField(null=True, blank=True)
    custom_rules = models.JSONField(default=dict, blank=True)

    bracket_type = models.CharField(max_length=24, choices=BracketType.choices,
                                    default=BracketType.SINGLE_ELIMINATION)
    max_participants = models.PositiveIntegerField(default=32)

    # --- Roster championship mode (kind == "roster"). All fields carry safe
    # defaults so a standard tournament ignores them entirely. -----------------
    kind = models.CharField(max_length=12, choices=TournamentKind.choices,
                            default=TournamentKind.STANDARD, db_index=True)
    format_kind = models.CharField(max_length=8, choices=FormatKind.choices,
                                   default=FormatKind.POINTS)
    league_double_round = models.BooleanField(default=False)
    rounds_count = models.PositiveSmallIntegerField(null=True, blank=True)
    seed_source = models.CharField(max_length=20, choices=SeedSource.choices,
                                   default=SeedSource.RANDOM)
    hybrid_advance_count = models.PositiveSmallIntegerField(null=True, blank=True)

    decks_per_player = models.PositiveSmallIntegerField(default=4)
    power_cap = models.PositiveSmallIntegerField(default=15)
    min_deck_power = models.PositiveSmallIntegerField(null=True, blank=True)
    max_deck_power = models.PositiveSmallIntegerField(null=True, blank=True)

    deck_selection_mode = models.CharField(max_length=24, choices=DeckSelectionMode.choices,
                                           default=DeckSelectionMode.RANDOM_ROTATION)
    random_options_count = models.PositiveSmallIntegerField(default=2)
    draw_timing = models.CharField(max_length=20, choices=DrawTiming.choices,
                                   default=DrawTiming.AUTO_ROUND_START)
    sequence_self_visibility = models.CharField(max_length=12,
                                                choices=SequenceSelfVisibility.choices,
                                                default=SequenceSelfVisibility.EACH_ROUND)
    sequence_opponent_visibility = models.CharField(max_length=8,
                                                    choices=SequenceOpponentVisibility.choices,
                                                    default=SequenceOpponentVisibility.HIDDEN)

    roster_visibility = models.CharField(max_length=8, choices=RosterVisibility.choices,
                                         default=RosterVisibility.PARTIAL)
    reveal_lists_after_end = models.BooleanField(default=True)

    ace_enabled = models.BooleanField(default=False)
    ace_rule = models.CharField(max_length=20, choices=AceRule.choices,
                                default=AceRule.VISUAL_ONLY)
    ace_reveal = models.CharField(max_length=24, choices=AceReveal.choices,
                                  default=AceReveal.PUBLIC)
    ace_required = models.BooleanField(default=False)

    allow_draws = models.BooleanField(default=True)
    points_win = models.PositiveSmallIntegerField(default=3)
    points_draw = models.PositiveSmallIntegerField(default=1)
    points_loss = models.PositiveSmallIntegerField(default=0)
    points_bye = models.PositiveSmallIntegerField(default=3)

    registration_opens_at = models.DateTimeField(null=True, blank=True)
    registration_closes_at = models.DateTimeField(null=True, blank=True)
    checkin_opens_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    starts_at = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=48, default="UTC")
    is_online = models.BooleanField(default=True)
    location = models.CharField(max_length=255, blank=True)
    online_link = models.URLField(blank=True)

    visibility = models.CharField(max_length=12, choices=Visibility.choices,
                                  default=Visibility.PUBLIC, db_index=True)
    invite_code = models.CharField(max_length=16, blank=True, db_index=True)
    auto_approve = models.BooleanField(default=True)

    requires_decklist = models.BooleanField(default=True)
    decklist_deadline = models.DateTimeField(null=True, blank=True)
    decklists_visibility = models.CharField(max_length=24, choices=DecklistVisibility.choices,
                                            default=DecklistVisibility.HIDDEN_UNTIL_START)
    decklist_reveal_at = models.DateTimeField(null=True, blank=True)

    requires_checkin = models.BooleanField(default=True)
    round_duration_minutes = models.PositiveIntegerField(default=40)
    best_of = models.PositiveSmallIntegerField(default=1)
    tiebreakers = models.JSONField(default=list, blank=True)
    prizes = models.TextField(blank=True)
    contact = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=16, choices=TournamentStatus.choices,
                              default=TournamentStatus.DRAFT, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["status", "visibility"])]

    def __str__(self) -> str:
        return self.name

    @property
    def is_roster(self) -> bool:
        return self.kind == TournamentKind.ROSTER

    def is_organizer(self, user) -> bool:
        if not (user and user.is_authenticated):
            return False
        return (
            self.organizer_id == user.id
            or user.is_platform_admin
            or self.staff.filter(user=user).exists()
        )


class TournamentStaff(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="staff")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    role = models.CharField(max_length=16, choices=StaffRole.choices, default=StaffRole.JUDGE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tournament", "user"], name="uniq_tournament_staff")
        ]


class TournamentRegistration(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="registrations")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="tournament_registrations")
    status = models.CharField(max_length=12, choices=RegistrationStatus.choices,
                              default=RegistrationStatus.PENDING, db_index=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tournament", "user"], name="uniq_registration")
        ]


class TournamentParticipant(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name="tournament_participations")
    seed = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=ParticipantStatus.choices,
                              default=ParticipantStatus.ACTIVE, db_index=True)
    dq_reason = models.CharField(max_length=255, blank=True)

    # standings cache
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    final_rank = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ("seed",)
        constraints = [
            models.UniqueConstraint(fields=["tournament", "user"], name="uniq_participant")
        ]

    def __str__(self) -> str:
        return f"{self.user.username} @ {self.tournament.name}"


class TournamentRulesSnapshot(BaseModel):
    """Immutable freeze of format rules + banlist + power policy at lock time."""

    tournament = models.OneToOneField(Tournament, on_delete=models.CASCADE,
                                      related_name="rules_snapshot")
    payload = models.JSONField(default=dict)
    content_hash = models.CharField(max_length=64, db_index=True)


class TournamentDeckSubmission(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="submissions")
    participant = models.OneToOneField(TournamentParticipant, on_delete=models.CASCADE,
                                       related_name="submission")
    source_deck = models.ForeignKey("decks.Deck", on_delete=models.SET_NULL, null=True,
                                    related_name="+")
    snapshot = models.ForeignKey("decks.DeckSnapshot", on_delete=models.SET_NULL, null=True,
                                 related_name="+")
    content_hash = models.CharField(max_length=64, db_index=True)
    payload = models.JSONField(default=dict)
    validation = models.JSONField(default=dict, blank=True)
    is_valid = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     null=True, related_name="+")

    def __str__(self) -> str:
        return f"submission {self.content_hash[:10]} · {self.participant_id}"


class TournamentCheckIn(BaseModel):
    participant = models.OneToOneField(TournamentParticipant, on_delete=models.CASCADE,
                                       related_name="check_in")
    checked_in_at = models.DateTimeField(auto_now_add=True)


class TournamentStage(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="stages")
    kind = models.CharField(max_length=24, choices=BracketType.choices)
    order = models.PositiveSmallIntegerField(default=1)
    name = models.CharField(max_length=80, default="Main")
    config = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=12, choices=RoundStatus.choices,
                              default=RoundStatus.PENDING)

    class Meta:
        ordering = ("order",)


class TournamentRound(BaseModel):
    stage = models.ForeignKey(TournamentStage, on_delete=models.CASCADE, related_name="rounds")
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=12, choices=RoundStatus.choices,
                              default=RoundStatus.PENDING)

    class Meta:
        ordering = ("number",)
        constraints = [
            models.UniqueConstraint(fields=["stage", "number"], name="uniq_stage_round")
        ]


class TournamentMatch(BaseModel):
    round = models.ForeignKey(TournamentRound, on_delete=models.CASCADE, related_name="matches")
    position = models.PositiveIntegerField(default=0)   # slot within the round (bracket layout)
    table_number = models.PositiveIntegerField(null=True, blank=True)
    room = models.CharField(max_length=64, blank=True)

    participant_a = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True,
                                      blank=True, related_name="matches_as_a")
    participant_b = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True,
                                      blank=True, related_name="matches_as_b")
    winner = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True,
                               blank=True, related_name="matches_won")

    state = models.CharField(max_length=12, choices=MatchState.choices,
                             default=MatchState.PENDING, db_index=True)
    best_of = models.PositiveSmallIntegerField(default=1)
    score_a = models.PositiveSmallIntegerField(default=0)
    score_b = models.PositiveSmallIntegerField(default=0)

    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    blank=True, related_name="+")
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                     blank=True, related_name="+")

    # winner advances into this slot of the next match (single/double elim)
    next_match = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="feeder_matches")
    next_slot = models.CharField(max_length=1, blank=True)  # 'a' or 'b'
    advanced = models.BooleanField(default=False)           # idempotency guard
    # loser drops here (double elimination)
    loser_next_match = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name="loser_feeder_matches")
    loser_next_slot = models.CharField(max_length=1, blank=True)
    loser_advanced = models.BooleanField(default=False)
    bracket = models.CharField(max_length=8, blank=True)    # '', 'winners', 'losers', 'grand'
    is_draw = models.BooleanField(default=False)            # Swiss / round robin

    scheduled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("position",)
        indexes = [models.Index(fields=["round", "position"])]

    def __str__(self) -> str:
        return f"M{self.position} R{self.round.number} [{self.state}]"


class TournamentGame(BaseModel):
    match = models.ForeignKey(TournamentMatch, on_delete=models.CASCADE, related_name="games")
    game_number = models.PositiveSmallIntegerField()
    winner = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True,
                               related_name="+")
    note = models.CharField(max_length=255, blank=True)


class MatchReport(BaseModel):
    match = models.ForeignKey(TournamentMatch, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                 related_name="+")
    score_a = models.PositiveSmallIntegerField(default=0)
    score_b = models.PositiveSmallIntegerField(default=0)
    winner = models.ForeignKey(TournamentParticipant, on_delete=models.SET_NULL, null=True,
                               related_name="+")
    confirmed = models.BooleanField(default=False)


class MatchDispute(BaseModel):
    match = models.ForeignKey(TournamentMatch, on_delete=models.CASCADE, related_name="disputes")
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name="+")
    reason = models.TextField()
    resolved = models.BooleanField(default=False)
    resolution = models.CharField(max_length=255, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name="+")


class TournamentStanding(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="standings")
    participant = models.ForeignKey(TournamentParticipant, on_delete=models.CASCADE,
                                    related_name="+")
    rank = models.PositiveIntegerField()
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    points = models.IntegerField(default=0)
    tiebreaks = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("rank",)
        constraints = [
            models.UniqueConstraint(fields=["tournament", "participant"], name="uniq_standing")
        ]


class TournamentAuditLog(BaseModel):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="audit_logs")
    action = models.CharField(max_length=48)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                              related_name="+")
    summary = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.action} @ {self.tournament_id}"


# =============================================================================
# Roster championship models (kind == "roster")
# =============================================================================
class TournamentRoster(BaseModel):
    """A participant's pool of decks for a roster championship. Sum of the
    owner-assigned deck powers must stay within the tournament's power_cap."""

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="rosters")
    participant = models.OneToOneField(TournamentParticipant, on_delete=models.CASCADE,
                                       related_name="roster")
    status = models.CharField(max_length=12, choices=RosterStatus.choices,
                              default=RosterStatus.DRAFT, db_index=True)
    power_used = models.PositiveSmallIntegerField(default=0)   # sum of assigned deck powers
    is_over_cap = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"roster {self.participant_id} @ {self.tournament_id}"


class RosterDeck(BaseModel):
    """One deck in a roster. `power` is assigned by the tournament OWNER (not the
    deck owner); `snapshot` freezes the decklist when the roster locks."""

    roster = models.ForeignKey(TournamentRoster, on_delete=models.CASCADE, related_name="decks")
    source_deck = models.ForeignKey("decks.Deck", on_delete=models.SET_NULL, null=True,
                                    related_name="+")
    snapshot = models.ForeignKey("decks.DeckSnapshot", on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name="+")
    power = models.PositiveSmallIntegerField(null=True, blank=True)  # owner-assigned
    power_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                 blank=True, related_name="+")
    is_ace = models.BooleanField(default=False)
    banlist_valid = models.BooleanField(default=True)
    is_valid = models.BooleanField(default=False)
    validation = models.JSONField(default=dict, blank=True)
    label = models.CharField(max_length=140, blank=True)   # frozen deck title
    slot = models.PositiveSmallIntegerField(default=0)
    order_index = models.PositiveSmallIntegerField(default=0)
    locked = models.BooleanField(default=False)

    class Meta:
        ordering = ("slot", "order_index")
        constraints = [
            models.UniqueConstraint(fields=["roster", "source_deck"], name="uniq_roster_deck")
        ]

    def __str__(self) -> str:
        return f"{self.label or self.source_deck_id} (power {self.power})"


class RosterDeckSequence(BaseModel):
    """Frozen predetermined draw order (deck_selection_mode == predetermined_order).
    Generated once at start; one row per (roster, round_number)."""

    roster = models.ForeignKey(TournamentRoster, on_delete=models.CASCADE, related_name="sequence")
    round_number = models.PositiveSmallIntegerField()
    roster_deck = models.ForeignKey(RosterDeck, on_delete=models.CASCADE, related_name="+")
    revealed = models.BooleanField(default=False)

    class Meta:
        ordering = ("round_number",)
        constraints = [
            models.UniqueConstraint(fields=["roster", "round_number"], name="uniq_roster_sequence")
        ]


class MatchDeckSelection(BaseModel):
    """The deck a participant will use in a specific match. Secret until BOTH
    sides confirm — `revealed` is only set once both selections are confirmed."""

    match = models.ForeignKey(TournamentMatch, on_delete=models.CASCADE,
                              related_name="deck_selections")
    participant = models.ForeignKey(TournamentParticipant, on_delete=models.CASCADE,
                                    related_name="deck_selections")
    roster_deck = models.ForeignKey(RosterDeck, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="selections")
    method = models.CharField(max_length=20, choices=SelectionMethod.choices,
                              default=SelectionMethod.RANDOM)
    confirmed = models.BooleanField(default=False)
    revealed = models.BooleanField(default=False)
    is_ace_used = models.BooleanField(default=False)
    options = models.JSONField(default=list, blank=True)    # choose_from_random: offered decks
    eligible = models.JSONField(default=list, blank=True)    # roster_deck uuids considered
    rule_used = models.CharField(max_length=32, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["match", "participant"], name="uniq_match_selection")
        ]

    def __str__(self) -> str:
        return f"selection {self.participant_id} @ match {self.match_id}"


class DeckDrawLog(BaseModel):
    """Immutable audit of every automatic draw. Never hand-edited; a re-draw sets
    admin_intervention=True and writes a NEW row."""

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="draw_logs")
    round = models.ForeignKey(TournamentRound, on_delete=models.SET_NULL, null=True,
                              related_name="draw_logs")
    participant = models.ForeignKey(TournamentParticipant, on_delete=models.CASCADE,
                                    related_name="draw_logs")
    result_deck = models.ForeignKey(RosterDeck, on_delete=models.SET_NULL, null=True,
                                    related_name="+")
    eligible = models.JSONField(default=list, blank=True)
    options = models.JSONField(default=list, blank=True)
    rule = models.CharField(max_length=32, blank=True)
    admin_intervention = models.BooleanField(default=False)
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                              blank=True, related_name="+")

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["tournament", "round"])]


class AceEvent(BaseModel):
    """Records Ace usage/reveal for rules that consume or expose the Ace."""

    roster = models.ForeignKey(TournamentRoster, on_delete=models.CASCADE, related_name="ace_events")
    match = models.ForeignKey(TournamentMatch, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="+")
    kind = models.CharField(max_length=16, choices=AceEventKind.choices)

    class Meta:
        ordering = ("-created_at",)


class TournamentPenalty(BaseModel):
    participant = models.ForeignKey(TournamentParticipant, on_delete=models.CASCADE,
                                    related_name="penalties")
    match = models.ForeignKey(TournamentMatch, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="+")
    kind = models.CharField(max_length=20, choices=PenaltyKind.choices)
    points = models.SmallIntegerField(default=0)   # points delta (negative = deduction)
    reason = models.CharField(max_length=255, blank=True)
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                  related_name="+")

    class Meta:
        ordering = ("-created_at",)
