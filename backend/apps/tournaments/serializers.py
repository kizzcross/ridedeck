from rest_framework import serializers

from .models import (
    MatchDispute,
    Tournament,
    TournamentDeckSubmission,
    TournamentMatch,
    TournamentParticipant,
    TournamentRegistration,
    TournamentRound,
    TournamentStage,
    TournamentStanding,
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
                  "organizer", "participant_count"]

    def get_participant_count(self, obj) -> int:
        return obj.participants.count()


class TournamentWriteSerializer(serializers.ModelSerializer):
    banlist_uuid = serializers.UUIDField(required=False, allow_null=True, write_only=True)
    power_policy_uuid = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Tournament
        fields = ["name", "description", "image", "format_code", "bracket_type",
                  "max_participants", "starts_at", "timezone", "is_online", "location",
                  "online_link", "visibility", "auto_approve", "requires_decklist",
                  "decklist_deadline", "decklists_visibility", "requires_checkin",
                  "round_duration_minutes", "best_of", "tiebreakers", "prizes", "contact",
                  "custom_rules", "banlist_uuid", "power_policy_uuid"]

    def _resolve(self, validated):
        from apps.banlists.models import Banlist
        from apps.powerlevel.models import TournamentPowerPolicy

        bl = validated.pop("banlist_uuid", None)
        pp = validated.pop("power_policy_uuid", None)
        if bl is not None:
            validated["banlist"] = Banlist.objects.filter(uuid=bl).first()
        if pp is not None:
            validated["power_policy"] = TournamentPowerPolicy.objects.filter(uuid=pp).first()
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
    power_policy = serializers.SerializerMethodField()

    class Meta:
        model = Tournament
        fields = ["uuid", "name", "description", "image", "format_code", "bracket_type",
                  "status", "visibility", "invite_code", "max_participants", "starts_at",
                  "timezone", "is_online", "location", "online_link", "auto_approve",
                  "requires_decklist", "decklist_deadline", "decklists_visibility",
                  "requires_checkin", "round_duration_minutes", "best_of", "tiebreakers",
                  "prizes", "contact", "banlist_uuid", "banlist_version_number",
                  "power_policy", "organizer", "is_organizer", "my_registration",
                  "participant_count", "created_at"]

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

    def get_power_policy(self, obj):
        return {"uuid": str(obj.power_policy.uuid), "kind": obj.power_policy.kind,
                "name": obj.power_policy.name} if obj.power_policy_id else None


class DisputeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchDispute
        fields = ["uuid", "reason", "resolved", "resolution", "created_at"]
