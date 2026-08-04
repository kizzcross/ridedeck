from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.cards.models import Card, CardPrinting

from .choices import Visibility
from .models import Deck, DeckComment, DeckFavorite, DeckLike, DeckSnapshot
from .serializers import (
    DeckCommentSerializer,
    DeckDetailSerializer,
    DeckListSerializer,
    DeckVersionSerializer,
    DeckWriteSerializer,
    SetEntrySerializer,
)
from .services import (
    ensure_working_version,
    fork_deck,
    set_entry,
    snapshot_hash,
)


class DeckViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "uuid"
    filterset_fields = ["format_code", "visibility", "nation_focus"]
    search_fields = ["title", "archetype"]
    ordering_fields = ["updated_at", "like_count", "favorite_count"]

    def get_queryset(self):
        user = self.request.user
        base = Deck.objects.filter(deleted_at__isnull=True).select_related(
            "owner__profile", "current_version", "cover_printing"
        )
        if self.action == "list":
            mine = self.request.query_params.get("mine")
            if mine and user.is_authenticated:
                return base.filter(owner=user)
            # public catalog (+ your own, whatever their visibility)
            q = Q(visibility=Visibility.PUBLIC)
            if user.is_authenticated:
                q |= Q(owner=user)
            return base.filter(q)
        return base

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return DeckWriteSerializer
        if self.action == "list":
            return DeckListSerializer
        return DeckDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deck = serializer.save(owner=request.user)
        ensure_working_version(deck)
        return Response(DeckDetailSerializer(deck, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    # Actions that mutate the deck itself require ownership; social actions
    # (fork/like/favorite/comment) only require that the deck be visible.
    OWNER_ACTIONS = {"update", "partial_update", "destroy", "entry", "publish", "snapshot"}

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        is_owner = user.is_authenticated and obj.owner_id == user.id
        is_admin = user.is_authenticated and user.is_platform_admin

        if self.action in self.OWNER_ACTIONS and not (is_owner or is_admin):
            raise PermissionDenied("Você não é dono deste deck.")
        # Visibility: private decks are only reachable by owner/admin.
        if obj.visibility == Visibility.PRIVATE and not (is_owner or is_admin):
            raise PermissionDenied("Este deck é privado.")
        return obj

    def retrieve(self, request, *args, **kwargs):
        deck = self.get_object()
        ensure_working_version(deck)
        return Response(DeckDetailSerializer(deck, context={"request": request}).data)

    def perform_destroy(self, instance):
        instance.soft_delete()

    # --- Builder actions --------------------------------------------------
    @extend_schema(request=SetEntrySerializer, responses=DeckVersionSerializer)
    @action(detail=True, methods=["post"], url_path="entry")
    def entry(self, request, uuid=None):
        deck = self.get_object()
        serializer = SetEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        card = Card.objects.filter(uuid=data["card"]).first()
        if not card:
            return Response({"error": {"code": "not_found", "message": "Carta não encontrada."}},
                            status=status.HTTP_404_NOT_FOUND)
        printing = None
        if data.get("preferred_printing"):
            printing = CardPrinting.objects.filter(uuid=data["preferred_printing"]).first()
        version = ensure_working_version(deck)
        set_entry(version, card, data["zone"], data["quantity"], printing)
        deck.save(update_fields=["updated_at"])
        version.refresh_from_db()
        return Response(DeckVersionSerializer(version).data)

    @action(detail=True, methods=["get"])
    def validate(self, request, uuid=None):
        deck = self.get_object()
        version = ensure_working_version(deck)
        owned = None
        if request.user.is_authenticated:
            from apps.collection.services import owned_map
            owned = owned_map(request.user)

        banlist_version = None
        from apps.banlists.models import Banlist
        banlist_uuid = request.query_params.get("banlist")
        bl = None
        if banlist_uuid:
            bl = Banlist.objects.filter(uuid=banlist_uuid).select_related("current_version").first()
        elif deck.check_banlist_id:
            bl = deck.check_banlist  # the deck's persisted checking banlist
        if bl:
            banlist_version = bl.current_version

        from apps.validation.service import validate_deck_version
        return Response(validate_deck_version(version, owned_map=owned,
                                              banlist_version=banlist_version))

    @action(detail=True, methods=["get"], url_path="power")
    def power(self, request, uuid=None):
        """Deck power stats (max, weighted avg, distribution, top contributors)."""
        from apps.powerlevel.services import deck_power_stats

        deck = self.get_object()
        version = ensure_working_version(deck)
        return Response(deck_power_stats(version, deck.format_code))

    @action(detail=True, methods=["get"], url_path="collection-report",
            permission_classes=[IsAuthenticated])
    def collection_report(self, request, uuid=None):
        """Owned vs. missing per card for the requesting user (+ shopping list).
        Purely informational — never affects deck validity."""
        from apps.collection.services import deck_collection_report

        deck = self.get_object()
        version = ensure_working_version(deck)
        return Response(deck_collection_report(version, request.user))

    @action(detail=True, methods=["post"])
    def publish(self, request, uuid=None):
        deck = self.get_object()
        vis = request.data.get("visibility", Visibility.PUBLIC)
        if vis not in Visibility.values:
            return Response({"error": {"code": "invalid", "message": "Visibilidade inválida."}},
                            status=status.HTTP_400_BAD_REQUEST)
        deck.visibility = vis
        deck.save(update_fields=["visibility"])
        return Response({"visibility": deck.visibility})

    @action(detail=True, methods=["post"])
    def fork(self, request, uuid=None):
        deck = self.get_object()  # retrieve-level visibility applies
        new_deck = fork_deck(deck, request.user)
        return Response(DeckDetailSerializer(new_deck, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def snapshot(self, request, uuid=None):
        deck = self.get_object()
        version = ensure_working_version(deck)
        from .services import _serialize_entries

        snap = DeckSnapshot.objects.create(
            deck=deck, version_number=version.version_number,
            payload={"entries": _serialize_entries(version), "format": deck.format_code},
            content_hash=snapshot_hash(version), created_by=request.user,
        )
        return Response({"uuid": str(snap.uuid), "content_hash": snap.content_hash},
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def like(self, request, uuid=None):
        deck = self.get_object()
        obj, created = DeckLike.objects.get_or_create(deck=deck, user=request.user)
        if not created:
            obj.delete()
        Deck.objects.filter(pk=deck.pk).update(like_count=deck.likes.count())
        return Response({"liked": created, "like_count": deck.likes.count()})

    @action(detail=True, methods=["post"])
    def favorite(self, request, uuid=None):
        deck = self.get_object()
        obj, created = DeckFavorite.objects.get_or_create(deck=deck, user=request.user)
        if not created:
            obj.delete()
        Deck.objects.filter(pk=deck.pk).update(favorite_count=deck.favorites.count())
        return Response({"favorited": created, "favorite_count": deck.favorites.count()})

    @action(detail=True, methods=["get", "post"], permission_classes=[IsAuthenticatedOrReadOnly])
    def comments(self, request, uuid=None):
        deck = self.get_object()
        if request.method == "POST":
            if not request.user.is_authenticated:
                raise PermissionDenied("Faça login para comentar.")
            body = (request.data.get("body") or "").strip()
            if not body:
                return Response({"error": {"code": "empty", "message": "Comentário vazio."}},
                                status=status.HTTP_400_BAD_REQUEST)
            with transaction.atomic():
                comment = DeckComment.objects.create(deck=deck, author=request.user, body=body[:2000])
            return Response(DeckCommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        page = self.paginate_queryset(deck.comments.select_related("author__profile"))
        return self.get_paginated_response(DeckCommentSerializer(page, many=True).data)
