from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.cards.models import Card
from apps.common.models import record_audit
from apps.common.permissions import IsPlatformAdmin

from .choices import BanlistCategory
from .models import (
    Banlist,
    BanlistComment,
    BanlistEntry,
    BanlistFavorite,
    BanlistLike,
    RestrictionGroup,
    RestrictionGroupMember,
)
from .serializers import (
    BanlistCommentSerializer,
    BanlistDetailSerializer,
    BanlistListSerializer,
    BanlistVersionSerializer,
    BanlistWriteSerializer,
    EntryWriteSerializer,
    GroupWriteSerializer,
)
from .services import ensure_draft_version, fork_banlist


class BanlistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "uuid"
    filterset_fields = ["category", "format_code"]
    search_fields = ["name", "objective"]
    ordering_fields = ["updated_at", "like_count"]

    OWNER_ACTIONS = {"update", "partial_update", "destroy", "entry", "group", "publish"}

    def get_queryset(self):
        user = self.request.user
        base = Banlist.objects.filter(deleted_at__isnull=True).select_related(
            "owner", "current_version"
        )
        if self.action == "list":
            # Another user's public/listed banlists (community browsing).
            owner = self.request.query_params.get("owner")
            if owner:
                q = Q(owner__username__iexact=owner) & (
                    Q(is_public=True, is_listed=True) | Q(category=BanlistCategory.OFFICIAL)
                )
                if user.is_authenticated:
                    q |= Q(owner__username__iexact=owner, owner=user)
                return base.filter(q)
            q = Q(category=BanlistCategory.OFFICIAL) | Q(is_public=True, is_listed=True)
            if user.is_authenticated:
                q |= Q(owner=user)
            return base.filter(q)
        return base

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BanlistWriteSerializer
        if self.action == "list":
            return BanlistListSerializer
        return BanlistDetailSerializer

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        is_owner = user.is_authenticated and obj.owner_id == user.id
        is_admin = user.is_authenticated and user.is_platform_admin
        if self.action in self.OWNER_ACTIONS and not (is_owner or is_admin):
            raise PermissionDenied("Você não é dono desta banlist.")
        if not obj.is_official and not obj.is_public and not (is_owner or is_admin):
            raise PermissionDenied("Banlist privada.")
        return obj

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # A normal user always creates a COMMUNITY banlist — never official.
        banlist = serializer.save(owner=request.user, category=BanlistCategory.COMMUNITY)
        ensure_draft_version(banlist)
        return Response(BanlistDetailSerializer(banlist, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        banlist = self.get_object()
        ensure_draft_version(banlist)
        return Response(BanlistDetailSerializer(banlist, context={"request": request}).data)

    def perform_destroy(self, instance):
        instance.soft_delete()

    # --- Editing ----------------------------------------------------------
    @extend_schema(request=EntryWriteSerializer, responses=BanlistVersionSerializer)
    @action(detail=True, methods=["post", "delete"], url_path="entry")
    def entry(self, request, uuid=None):
        banlist = self.get_object()
        version = ensure_draft_version(banlist)
        if request.method == "DELETE":
            BanlistEntry.objects.filter(version=version, uuid=request.data.get("entry")).delete()
        else:
            s = EntryWriteSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            d = s.validated_data
            card = Card.objects.filter(uuid=d["card"]).first() if d.get("card") else None
            group = version.restriction_groups.filter(uuid=d["group"]).first() if d.get("group") else None
            BanlistEntry.objects.create(
                version=version, restriction_type=d["restriction_type"], card=card,
                group=group, limit_value=d.get("limit_value"), note=d.get("note", ""),
            )
        banlist.save(update_fields=["updated_at"])
        version.refresh_from_db()
        return Response(BanlistVersionSerializer(version).data)

    @extend_schema(request=GroupWriteSerializer)
    @action(detail=True, methods=["post"], url_path="group")
    def group(self, request, uuid=None):
        banlist = self.get_object()
        version = ensure_draft_version(banlist)
        s = GroupWriteSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        with transaction.atomic():
            grp = RestrictionGroup.objects.create(
                version=version, name=d["name"], kind=d["kind"], limit_value=d["limit_value"])
            for card in Card.objects.filter(uuid__in=d["members"]):
                RestrictionGroupMember.objects.create(group=grp, card=card)
        version.refresh_from_db()
        return Response(BanlistVersionSerializer(version).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="make-official",
            permission_classes=[IsPlatformAdmin])
    def make_official(self, request, uuid=None):
        """ONLY a Platform Admin can mark a banlist official (or revert it).
        A community banlist never appears official without this action."""
        banlist = super().get_object()  # bypass OWNER_ACTIONS check; admin gate is here
        official = request.data.get("official", True)
        previous = banlist.category
        banlist.category = BanlistCategory.OFFICIAL if official else BanlistCategory.COMMUNITY
        if official:
            banlist.is_public = True
            banlist.is_listed = True
        banlist.save(update_fields=["category", "is_public", "is_listed"])
        record_audit(action="banlist_official_change", actor=request.user, target=banlist,
                     summary=f"{previous} → {banlist.category}",
                     payload={"banlist": banlist.name, "previous": previous,
                              "new": banlist.category})
        return Response({"category": banlist.category, "is_official": banlist.is_official})

    @action(detail=True, methods=["get"], url_path="restriction-map")
    def restriction_map(self, request, uuid=None):
        """{card_uuid: {type, limit, group}} for the current version — lets the
        deck builder mark banned/limited cards inline."""
        banlist = self.get_object()
        version = banlist.current_version
        result: dict[str, dict] = {}
        if not version:
            return Response({"format_code": banlist.format_code, "restrictions": {}})
        for entry in version.entries.select_related("card", "group").prefetch_related(
                "group__members__card"):
            if entry.card_id:
                result[str(entry.card.uuid)] = {
                    "type": entry.restriction_type,
                    "limit": entry.effective_limit(),
                }
            elif entry.group_id:
                for m in entry.group.members.all():
                    result.setdefault(str(m.card.uuid), {
                        "type": entry.restriction_type,
                        "limit": entry.group.limit_value,
                        "group": entry.group.name,
                        "group_kind": entry.group.kind,
                    })
        return Response({"format_code": banlist.format_code, "restrictions": result})

    @action(detail=True, methods=["post"])
    def fork(self, request, uuid=None):
        banlist = self.get_object()
        new = fork_banlist(banlist, request.user)
        return Response(BanlistDetailSerializer(new, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def like(self, request, uuid=None):
        banlist = self.get_object()
        obj, created = BanlistLike.objects.get_or_create(banlist=banlist, user=request.user)
        if not created:
            obj.delete()
        Banlist.objects.filter(pk=banlist.pk).update(like_count=banlist.likes.count())
        return Response({"liked": created, "like_count": banlist.likes.count()})

    @action(detail=True, methods=["post"])
    def favorite(self, request, uuid=None):
        banlist = self.get_object()
        obj, created = BanlistFavorite.objects.get_or_create(banlist=banlist, user=request.user)
        if not created:
            obj.delete()
        Banlist.objects.filter(pk=banlist.pk).update(favorite_count=banlist.favorites.count())
        return Response({"favorited": created})

    @action(detail=True, methods=["get", "post"])
    def comments(self, request, uuid=None):
        banlist = self.get_object()
        if request.method == "POST":
            if not request.user.is_authenticated:
                raise PermissionDenied("Faça login.")
            body = (request.data.get("body") or "").strip()
            if not body:
                return Response({"error": {"code": "empty", "message": "Vazio."}},
                                status=status.HTTP_400_BAD_REQUEST)
            c = BanlistComment.objects.create(banlist=banlist, author=request.user, body=body[:2000])
            return Response(BanlistCommentSerializer(c).data, status=status.HTTP_201_CREATED)
        return Response(BanlistCommentSerializer(banlist.comments.all(), many=True).data)
