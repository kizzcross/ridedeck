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
    BracketType,
    DecklistVisibility,
    MatchState,
    ParticipantStatus,
    RegistrationStatus,
    RoundStatus,
    StaffRole,
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
    power_policy = models.ForeignKey("powerlevel.TournamentPowerPolicy", on_delete=models.SET_NULL,
                                     null=True, blank=True, related_name="tournaments")
    custom_rules = models.JSONField(default=dict, blank=True)

    bracket_type = models.CharField(max_length=24, choices=BracketType.choices,
                                    default=BracketType.SINGLE_ELIMINATION)
    max_participants = models.PositiveIntegerField(default=32)

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
