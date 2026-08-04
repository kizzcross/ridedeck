from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.decks.models import Deck

from .choices import TournamentStatus, Visibility
from .models import (
    MatchDispute,
    Tournament,
    TournamentMatch,
    TournamentRegistration,
)
from .serializers import (
    MatchSerializer,
    ParticipantSerializer,
    RegistrationSerializer,
    StageSerializer,
    StandingSerializer,
    SubmissionSerializer,
    TournamentDetailSerializer,
    TournamentListSerializer,
    TournamentWriteSerializer,
)
from .services import (
    audit,
    check_in,
    confirm_result,
    disqualify,
    lock_registration,
    open_registration,
    organizer_set_result,
    register,
    report_result,
    seed_participants,
    set_registration_status,
    submit_deck,
)


class TournamentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "uuid"
    filterset_fields = ["status", "format_code", "bracket_type"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "starts_at"]

    def get_queryset(self):
        user = self.request.user
        base = Tournament.objects.filter(deleted_at__isnull=True).select_related("organizer__profile")
        if self.action == "list":
            q = Q(visibility=Visibility.PUBLIC)
            if user.is_authenticated:
                q |= Q(organizer=user) | Q(staff__user=user)
            return base.filter(q).distinct()
        return base

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TournamentWriteSerializer
        if self.action == "list":
            return TournamentListSerializer
        return TournamentDetailSerializer

    def _organizer_guard(self, tournament):
        if not tournament.is_organizer(self.request.user):
            raise PermissionDenied("Você não organiza este torneio.")

    def create(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        tournament = s.save(organizer=request.user)
        return Response(TournamentDetailSerializer(tournament, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    def get_object(self):
        obj = super().get_object()
        if self.action in ("update", "partial_update", "destroy"):
            self._organizer_guard(obj)
        if obj.visibility == Visibility.PRIVATE and not obj.is_organizer(self.request.user):
            # unlisted is reachable by link; private only organizer/staff/admin
            if obj.visibility == Visibility.PRIVATE:
                raise PermissionDenied("Torneio privado.")
        return obj

    def retrieve(self, request, *args, **kwargs):
        t = self.get_object()
        return Response(TournamentDetailSerializer(t, context={"request": request}).data)

    def perform_destroy(self, instance):
        instance.soft_delete()

    # --- Lifecycle (organizer) -------------------------------------------
    @action(detail=True, methods=["post"], url_path="open-registration")
    def open_registration(self, request, uuid=None):
        t = self.get_object()
        self._organizer_guard(t)
        open_registration(t, request.user)
        return Response(TournamentDetailSerializer(t, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def lock(self, request, uuid=None):
        t = self.get_object()
        self._organizer_guard(t)
        lock_registration(t, request.user)
        return Response({"status": t.status})

    @action(detail=True, methods=["post"], url_path="generate-bracket")
    def generate_bracket(self, request, uuid=None):
        t = self.get_object()
        self._organizer_guard(t)
        from .formats import dispatch_generate
        try:
            dispatch_generate(t, request.user)
        except ValueError as e:
            raise ValidationError(str(e)) from e
        return Response({"status": t.status}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def seeding(self, request, uuid=None):
        t = self.get_object()
        self._organizer_guard(t)
        seed_participants(t, order=request.data.get("order"))
        return Response(ParticipantSerializer(
            t.participants.order_by("seed"), many=True).data)

    # --- Registration / participation ------------------------------------
    @action(detail=True, methods=["post"])
    def register(self, request, uuid=None):
        if not request.user.is_authenticated:
            raise PermissionDenied("Faça login para se inscrever.")
        t = self.get_object()
        if t.status != TournamentStatus.REGISTRATION:
            raise ValidationError("Inscrições não estão abertas.")
        if t.participants.count() >= t.max_participants and t.auto_approve:
            raise ValidationError("Torneio lotado.")
        reg = register(t, request.user, note=request.data.get("note", ""))
        return Response(RegistrationSerializer(reg).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def registrations(self, request, uuid=None):
        t = self.get_object()
        self._organizer_guard(t)
        return Response(RegistrationSerializer(t.registrations.select_related("user__profile"),
                                               many=True).data)

    @action(detail=True, methods=["post"], url_path="review-registration")
    def review_registration(self, request, uuid=None):
        t = self.get_object()
        self._organizer_guard(t)
        reg = TournamentRegistration.objects.filter(
            tournament=t, uuid=request.data.get("registration")).first()
        if not reg:
            return Response({"error": {"code": "not_found", "message": "Inscrição não encontrada."}},
                            status=status.HTTP_404_NOT_FOUND)
        set_registration_status(reg, request.data.get("status"), request.user)
        return Response(RegistrationSerializer(reg).data)

    @action(detail=True, methods=["get"])
    def participants(self, request, uuid=None):
        t = self.get_object()
        return Response(ParticipantSerializer(
            t.participants.select_related("user__profile").order_by("seed"), many=True).data)

    @action(detail=True, methods=["post"], url_path="check-in")
    def check_in(self, request, uuid=None):
        t = self.get_object()
        p = t.participants.filter(user=request.user).first()
        if not p:
            raise PermissionDenied("Você não é participante.")
        check_in(t, p)
        return Response({"checked_in": True})

    @action(detail=True, methods=["post"], url_path="disqualify")
    def disqualify(self, request, uuid=None):
        t = self.get_object()
        self._organizer_guard(t)
        p = t.participants.filter(uuid=request.data.get("participant")).first()
        if not p:
            return Response(status=status.HTTP_404_NOT_FOUND)
        disqualify(p, request.user, reason=request.data.get("reason", ""))
        return Response(ParticipantSerializer(p).data)

    # --- Deck submission --------------------------------------------------
    @action(detail=True, methods=["post"], url_path="submit-deck")
    def submit_deck(self, request, uuid=None):
        t = self.get_object()
        p = t.participants.filter(user=request.user).first()
        if not p:
            raise PermissionDenied("Inscreva-se antes de submeter um deck.")
        deck = Deck.objects.filter(uuid=request.data.get("deck"), owner=request.user).first()
        if not deck:
            return Response({"error": {"code": "not_found", "message": "Deck não encontrado."}},
                            status=status.HTTP_404_NOT_FOUND)
        if hasattr(p, "submission") and p.submission.locked:
            raise ValidationError("Submissão travada — não pode mais ser alterada.")
        sub = submit_deck(t, p, deck, request.user)
        return Response(SubmissionSerializer(sub).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="my-submission")
    def my_submission(self, request, uuid=None):
        t = self.get_object()
        p = t.participants.filter(user=request.user).first()
        if not p or not hasattr(p, "submission"):
            return Response({"submission": None})
        return Response(SubmissionSerializer(p.submission).data)

    # --- Bracket + standings ---------------------------------------------
    @action(detail=True, methods=["get"])
    def bracket(self, request, uuid=None):
        t = self.get_object()
        stages = t.stages.prefetch_related(
            "rounds__matches__participant_a__user__profile",
            "rounds__matches__participant_b__user__profile",
        )
        return Response(StageSerializer(stages, many=True).data)

    @action(detail=True, methods=["get"])
    def standings(self, request, uuid=None):
        t = self.get_object()
        return Response(StandingSerializer(
            t.standings.select_related("participant__user__profile"), many=True).data)


class MatchViewSet(viewsets.GenericViewSet):
    """Match reporting: participants report + confirm; organizer overrides."""

    permission_classes = [IsAuthenticated]
    lookup_field = "uuid"
    queryset = TournamentMatch.objects.all()

    def _match(self):
        return TournamentMatch.objects.select_related(
            "round__stage__tournament", "participant_a__user", "participant_b__user"
        ).get(uuid=self.kwargs["uuid"])

    def _is_participant(self, match, user):
        return user.id in {getattr(match.participant_a, "user_id", None),
                           getattr(match.participant_b, "user_id", None)}

    @extend_schema(request={"application/json": {"type": "object", "properties": {
        "score_a": {"type": "integer"}, "score_b": {"type": "integer"}}}})
    @action(detail=True, methods=["post"])
    def report(self, request, uuid=None):
        match = self._match()
        t = match.round.stage.tournament
        if not (self._is_participant(match, request.user) or t.is_organizer(request.user)):
            raise PermissionDenied("Você não joga esta partida.")
        try:
            m = report_result(str(match.uuid), request.user,
                              int(request.data.get("score_a", 0)), int(request.data.get("score_b", 0)))
        except ValueError as e:
            raise ValidationError(str(e)) from e
        return Response(MatchSerializer(m).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, uuid=None):
        match = self._match()
        t = match.round.stage.tournament
        organizer = t.is_organizer(request.user)
        # The confirmer must be the *opponent* of the reporter, or the organizer.
        if not (self._is_participant(match, request.user) or organizer):
            raise PermissionDenied("Você não joga esta partida.")
        if match.reported_by_id == request.user.id and not organizer:
            raise ValidationError("Quem reportou não pode confirmar — aguarde o oponente.")
        try:
            m = confirm_result(str(match.uuid), request.user, force=organizer)
        except ValueError as e:
            raise ValidationError(str(e)) from e
        return Response(MatchSerializer(m).data)

    @action(detail=True, methods=["post"], url_path="set-result")
    def set_result(self, request, uuid=None):
        match = self._match()
        t = match.round.stage.tournament
        if not t.is_organizer(request.user):
            raise PermissionDenied("Apenas o organizador pode ajustar resultados.")
        m = organizer_set_result(str(match.uuid), request.user,
                                 int(request.data.get("score_a", 0)),
                                 int(request.data.get("score_b", 0)))
        return Response(MatchSerializer(m).data)

    @action(detail=True, methods=["post"])
    def dispute(self, request, uuid=None):
        match = self._match()
        if not self._is_participant(match, request.user):
            raise PermissionDenied("Você não joga esta partida.")
        from .choices import MatchState
        match.state = MatchState.DISPUTED
        match.save(update_fields=["state"])
        MatchDispute.objects.create(match=match, opened_by=request.user,
                                    reason=request.data.get("reason", ""))
        audit(match.round.stage.tournament, "match_disputed", request.user,
              f"Disputa aberta na partida {match.position}")
        return Response(MatchSerializer(match).data)
