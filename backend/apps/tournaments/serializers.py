from rest_framework import serializers

from .models import (
    MatchDispute,
    RosterDeck,
    Tournament,
    TournamentDeckSubmission,
    TournamentMatch,
    TournamentParticipant,
    TournamentRegistration,
    TournamentRoster,
    TournamentRound,
    TournamentStage,
    TournamentStanding,
)

# Roster-championship config fields shared by the write + detail serializers.
ROSTER_CONFIG_FIELDS = (
    "kind", "format_kind", "league_double_round", "rounds_count", "seed_source",
    "hybrid_advance_count", "decks_per_player", "power_cap", "min_deck_power",
    "max_deck_power", "deck_selection_mode", "random_options_count", "draw_timing",
    "sequence_self_visibility", "sequence_opponent_visibility", "roster_visibility",
    "reveal_lists_after_end", "ace_enabled", "ace_rule", "ace_reveal", "ace_required",
    "allow_draws", "points_win", "points_draw", "points_loss", "points_bye",
    "registration_opens_at", "registration_closes_at", "checkin_opens_at", "ends_at",
)


class UserMiniSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()
    username = serializers.CharField()
    avatar_key = serializers.SerializerMethodField()

    def get_avatar_key(self, obj) -> str:
        return getattr(getattr(obj, "profile", None), "avatar_key", "")


class TournamentListSerializer(serializers.ModelSerializer):
    organizer = UserMiniSerializer(read_only=True)
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Tournament
        fields = ["uuid", "name", "image", "format_code", "bracket_type", "status",
                  "visibility", "is_online", "starts_at", "max_participants",
                  "organizer", "participant_count", "kind", "format_kind"]

    def get_participant_count(self, obj) -> int:
        return obj.participants.count()


class TournamentWriteSerializer(serializers.ModelSerializer):
    banlist_uuid = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Tournament
        fields = ["name", "description", "image", "format_code", "bracket_type",
                  "max_participants", "starts_at", "timezone", "is_online", "location",
                  "online_link", "visibility", "auto_approve", "requires_decklist",
                  "decklist_deadline", "decklists_visibility", "requires_checkin",
                  "round_duration_minutes", "best_of", "tiebreakers", "prizes", "contact",
                  "custom_rules", "banlist_uuid", *ROSTER_CONFIG_FIELDS]

    def _resolve(self, validated):
        from apps.banlists.models import Banlist

        bl = validated.pop("banlist_uuid", None)
        if bl is not None:
            validated["banlist"] = Banlist.objects.filter(uuid=bl).first()
        return validated

    def create(self, validated_data):
        return super().create(self._resolve(validated_data))

    def update(self, instance, validated_data):
        return super().update(instance, self._resolve(validated_data))


class ParticipantSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    checked_in = serializers.SerializerMethodField()
    has_submission = serializers.SerializerMethodField()

    class Meta:
        model = TournamentParticipant
        fields = ["uuid", "user", "seed", "status", "wins", "losses", "final_rank",
                  "checked_in", "has_submission"]

    def get_checked_in(self, obj) -> bool:
        return hasattr(obj, "check_in")

    def get_has_submission(self, obj) -> bool:
        return hasattr(obj, "submission")


class RegistrationSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = TournamentRegistration
        fields = ["uuid", "user", "status", "note", "created_at"]


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TournamentDeckSubmission
        fields = ["uuid", "content_hash", "is_valid", "locked", "validation", "payload",
                  "created_at"]


class RosterDeckSerializer(serializers.ModelSerializer):
    deck_uuid = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()
    suggested_power = serializers.SerializerMethodField()

    class Meta:
        model = RosterDeck
        fields = ["uuid", "deck_uuid", "label", "power", "suggested_power", "is_ace",
                  "banlist_valid", "is_valid", "slot", "order_index", "locked", "cover_image"]

    def get_deck_uuid(self, obj):
        return str(obj.source_deck.uuid) if obj.source_deck_id else None

    def get_cover_image(self, obj):
        deck = obj.source_deck
        if deck and deck.cover_printing_id:
            return deck.cover_printing.image_url
        return None

    def get_suggested_power(self, obj):
        return obj.source_deck.power_stars if obj.source_deck_id else None


class RosterSerializer(serializers.ModelSerializer):
    participant = ParticipantSerializer(read_only=True)
    decks = RosterDeckSerializer(many=True, read_only=True)
    power_cap = serializers.SerializerMethodField()
    decks_per_player = serializers.SerializerMethodField()

    class Meta:
        model = TournamentRoster
        fields = ["uuid", "participant", "status", "power_used", "is_over_cap", "power_cap",
                  "decks_per_player", "confirmed_at", "decks"]

    def get_power_cap(self, obj) -> int:
        return obj.tournament.power_cap

    def get_decks_per_player(self, obj) -> int:
        return obj.tournament.decks_per_player


class MatchSelectionSerializer(serializers.Serializer):
    """A participant's deck selection, gating the opponent's deck until reveal.
    The deck is shown only when revealed, or to its owner, or to the organizer."""

    participant_uuid = serializers.SerializerMethodField()
    method = serializers.CharField()
    confirmed = serializers.BooleanField()
    revealed = serializers.BooleanField()
    is_ace_used = serializers.BooleanField()
    deck = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()

    def get_participant_uuid(self, obj):
        return str(obj.participant.uuid)

    def _can_see(self, obj) -> bool:
        request = self.context.get("request")
        if obj.revealed:
            return True
        if not request or not request.user.is_authenticated:
            return False
        tournament = self.context.get("tournament")
        return obj.participant.user_id == request.user.id or (
            tournament and tournament.is_organizer(request.user))

    @staticmethod
    def _deck_repr(rd):
        if not rd:
            return None
        cover = rd.source_deck.cover_printing.image_url if (
            rd.source_deck_id and rd.source_deck.cover_printing_id) else None
        return {"uuid": str(rd.uuid), "label": rd.label, "is_ace": rd.is_ace, "cover_image": cover}

    def get_deck(self, obj):
        if obj.roster_deck_id and self._can_see(obj):
            return self._deck_repr(obj.roster_deck)
        return None

    def get_options(self, obj):
        # Offered options are visible only to the deciding player (secret pick).
        request = self.context.get("request")
        if not (request and obj.participant.user_id == getattr(request.user, "id", None)):
            return []
        from .models import RosterDeck
        rds = RosterDeck.objects.filter(uuid__in=obj.options or [])
        return [self._deck_repr(rd) for rd in rds]


class RosterMatchSerializer(serializers.ModelSerializer):
    participant_a = ParticipantSerializer(read_only=True)
    participant_b = ParticipantSerializer(read_only=True)
    selections = serializers.SerializerMethodField()
    winner_uuid = serializers.SerializerMethodField()

    class Meta:
        model = TournamentMatch
        fields = ["uuid", "position", "table_number", "state", "participant_a", "participant_b",
                  "winner_uuid", "score_a", "score_b", "selections"]

    def get_winner_uuid(self, obj):
        return str(obj.winner.uuid) if obj.winner_id else None

    def get_selections(self, obj):
        sels = obj.deck_selections.select_related("participant__user", "roster_deck__source_deck__cover_printing")
        return MatchSelectionSerializer(sels, many=True, context=self.context).data


class MatchSerializer(serializers.ModelSerializer):
    participant_a = ParticipantSerializer(read_only=True)
    participant_b = ParticipantSerializer(read_only=True)
    winner_uuid = serializers.SerializerMethodField()

    class Meta:
        model = TournamentMatch
        fields = ["uuid", "position", "table_number", "room", "state", "best_of",
                  "score_a", "score_b", "participant_a", "participant_b", "winner_uuid",
                  "next_match", "next_slot", "scheduled_at"]

    def get_winner_uuid(self, obj):
        return str(obj.winner.uuid) if obj.winner_id else None


class RoundSerializer(serializers.ModelSerializer):
    matches = MatchSerializer(many=True, read_only=True)

    class Meta:
        model = TournamentRound
        fields = ["uuid", "number", "name", "status", "matches"]


class StageSerializer(serializers.ModelSerializer):
    rounds = RoundSerializer(many=True, read_only=True)

    class Meta:
        model = TournamentStage
        fields = ["uuid", "kind", "name", "status", "rounds"]


class StandingSerializer(serializers.ModelSerializer):
    participant = ParticipantSerializer(read_only=True)

    class Meta:
        model = TournamentStanding
        fields = ["rank", "wins", "losses", "draws", "points", "tiebreaks", "participant"]


class TournamentDetailSerializer(serializers.ModelSerializer):
    organizer = UserMiniSerializer(read_only=True)
    is_organizer = serializers.SerializerMethodField()
    my_registration = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    banlist_uuid = serializers.SerializerMethodField()

    class Meta:
        model = Tournament
        fields = ["uuid", "name", "description", "image", "format_code", "bracket_type",
                  "status", "visibility", "invite_code", "max_participants", "starts_at",
                  "timezone", "is_online", "location", "online_link", "auto_approve",
                  "requires_decklist", "decklist_deadline", "decklists_visibility",
                  "requires_checkin", "round_duration_minutes", "best_of", "tiebreakers",
                  "prizes", "contact", "banlist_uuid", "banlist_version_number",
                  "organizer", "is_organizer", "my_registration",
                  "participant_count", "created_at", *ROSTER_CONFIG_FIELDS]

    def get_is_organizer(self, obj) -> bool:
        request = self.context.get("request")
        return obj.is_organizer(request.user) if request else False

    def get_my_registration(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        reg = obj.registrations.filter(user=request.user).first()
        return {"status": reg.status} if reg else None

    def get_participant_count(self, obj) -> int:
        return obj.participants.count()

    def get_banlist_uuid(self, obj):
        return str(obj.banlist.uuid) if obj.banlist_id else None


class DisputeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchDispute
        fields = ["uuid", "reason", "resolved", "resolution", "created_at"]
