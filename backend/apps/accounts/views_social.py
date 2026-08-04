"""Social endpoints: friends, friend requests, favorite cards, avatar options."""
from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cards.models import Card
from apps.common.models import record_audit
from apps.common.permissions import IsPlatformAdmin

from .choices import PlatformRole
from .models import FavoriteCard, Friendship
from .serializers import (
    FavoriteCardSerializer,
    FriendshipSerializer,
    MiniUserSerializer,
)
from .services import (
    accept_friend_request,
    remove_or_reject,
    send_friend_request,
)

User = get_user_model()

# The preset avatars users can pick (pixel nation logos, for now).
AVATAR_OPTIONS = [
    {"key": f"nation:{slug}", "label": label, "nation": slug}
    for slug, label in [
        ("dragon_empire", "Dragon Empire"),
        ("dark_states", "Dark States"),
        ("brandt_gate", "Brandt Gate"),
        ("keter_sanctuary", "Keter Sanctuary"),
        ("stoicheia", "Stoicheia"),
        ("lyrical_monasterio", "Lyrical Monasterio"),
        ("united_sanctuary", "United Sanctuary"),
        ("dark_zone", "Dark Zone"),
        ("magallanica", "Magallanica"),
        ("zoo", "Zoo"),
        ("star_gate", "Star Gate"),
    ]
]


class PromoteUserView(APIView):
    """A Platform Admin can promote another user (e.g. a friend) to Platform
    Admin, or demote one. Admin-only + audited. Self-demotion is blocked to
    avoid locking out the last admin."""

    permission_classes = [IsPlatformAdmin]

    @extend_schema(request={"application/json": {"type": "object", "properties": {
        "username": {"type": "string"}, "promote": {"type": "boolean"}}}})
    def post(self, request):
        username = (request.data.get("username") or "").strip()
        promote = request.data.get("promote", True)
        target = User.objects.filter(username__iexact=username, is_active=True).first()
        if not target:
            return Response({"error": {"code": "not_found", "message": "Usuário não encontrado."}},
                            status=status.HTTP_404_NOT_FOUND)
        if not promote and target.id == request.user.id:
            return Response({"error": {"code": "self_demote",
                            "message": "Você não pode rebaixar a si mesmo."}},
                            status=status.HTTP_400_BAD_REQUEST)

        previous = target.role
        if promote:
            target.promote_to_platform_admin()
        else:
            target.role = PlatformRole.MEMBER
            target.is_staff = False
            target.is_superuser = False
            target.save(update_fields=["role", "is_staff", "is_superuser"])

        record_audit(
            action="admin_action", actor=request.user, target=target,
            summary=f"Role {previous} → {target.role}",
            payload={"target": target.username, "previous_role": previous,
                     "new_role": target.role},
        )
        return Response({"username": target.username, "role": target.role,
                         "is_platform_admin": target.is_platform_admin})


class AvatarOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: dict})
    def get(self, request):
        return Response({"options": AVATAR_OPTIONS})


class FriendshipViewSet(viewsets.GenericViewSet):
    """Friends + requests. Uses uuid lookups."""

    permission_classes = [IsAuthenticated]
    serializer_class = FriendshipSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        user = self.request.user
        return Friendship.objects.filter(
            Q(requester=user) | Q(addressee=user)
        ).select_related("requester__profile", "addressee__profile")

    @action(detail=False, methods=["get"])
    def friends(self, request):
        """Accepted friendships."""
        users = Friendship.friends_of(request.user).select_related("profile")
        return Response(MiniUserSerializer(users, many=True).data)

    @action(detail=False, methods=["get"])
    def requests(self, request):
        """Pending requests, split into incoming/outgoing."""
        pending = self.get_queryset().filter(status=Friendship.Status.PENDING)
        ser = FriendshipSerializer(pending, many=True, context={"request": request})
        incoming = [f for f in ser.data if f["direction"] == "incoming"]
        outgoing = [f for f in ser.data if f["direction"] == "outgoing"]
        return Response({"incoming": incoming, "outgoing": outgoing})

    @extend_schema(request={"application/json": {"type": "object",
                   "properties": {"username": {"type": "string"}}}})
    @action(detail=False, methods=["post"], url_path="add")
    def add(self, request):
        username = (request.data.get("username") or "").strip()
        target = User.objects.filter(username__iexact=username, is_active=True).first()
        if not target:
            return Response({"error": {"code": "not_found", "message": "Usuário não encontrado."}},
                            status=status.HTTP_404_NOT_FOUND)
        friendship = send_friend_request(request.user, target)
        return Response(FriendshipSerializer(friendship, context={"request": request}).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def accept(self, request, uuid=None):
        friendship = self.get_object()
        accept_friend_request(friendship, request.user)
        return Response(FriendshipSerializer(friendship, context={"request": request}).data)

    def destroy(self, request, uuid=None):
        """Reject / cancel / unfriend."""
        friendship = self.get_object()
        remove_or_reject(friendship, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteCardView(ListCreateAPIView):
    """GET my favorites · POST {card} to toggle."""

    permission_classes = [IsAuthenticated]
    serializer_class = FavoriteCardSerializer

    def get_queryset(self):
        return (
            FavoriteCard.objects.filter(user=self.request.user)
            .select_related("card")
            .prefetch_related("card__printings")
            .order_by("-created_at")
        )

    @extend_schema(request={"application/json": {"type": "object",
                   "properties": {"card": {"type": "string", "description": "card uuid"}}}})
    def post(self, request, *args, **kwargs):
        card_uuid = request.data.get("card")
        card = Card.objects.filter(uuid=card_uuid).first()
        if not card:
            return Response({"error": {"code": "not_found", "message": "Carta não encontrada."}},
                            status=status.HTTP_404_NOT_FOUND)
        fav, created = FavoriteCard.objects.get_or_create(user=request.user, card=card)
        if not created:
            fav.delete()
            return Response({"favorited": False})
        return Response({"favorited": True}, status=status.HTTP_201_CREATED)


class MyFavoriteIdsView(APIView):
    """Lightweight list of favorited card uuids for the current user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        ids = list(
            FavoriteCard.objects.filter(user=request.user).values_list("card__uuid", flat=True)
        )
        return Response({"card_uuids": [str(u) for u in ids]})
