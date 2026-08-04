from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cards.models import CardPrinting

from .models import TradeItem, UserCollectionItem, WishlistItem
from .serializers import (
    CollectionItemSerializer,
    SetOwnedSerializer,
    TradeSerializer,
    WishlistSerializer,
)
from .services import owned_map, upsert_owned


class CollectionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """The user's owned cards, grouped by identity."""

    permission_classes = [IsAuthenticated]
    serializer_class = CollectionItemSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        qs = (
            UserCollectionItem.objects.filter(user=self.request.user)
            .select_related("card")
            .prefetch_related("printings__printing__card_set", "card__printings")
            .order_by("card__grade", "card__name")
        )
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(card__name__icontains=search)
        return qs

    @action(detail=False, methods=["post"], url_path="set")
    def set_owned(self, request):
        serializer = SetOwnedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        printing = CardPrinting.objects.filter(uuid=data["printing"]).select_related("card").first()
        if not printing:
            return Response({"error": {"code": "not_found", "message": "Printing não encontrada."}},
                            status=status.HTTP_404_NOT_FOUND)
        upsert_owned(
            request.user, printing, quantity=data["quantity"], condition=data["condition"],
            language=data["language"], finish=data.get("finish", ""),
            price_paid=data.get("price_paid"),
        )
        return Response({"ok": True, "card_uuid": str(printing.card.uuid),
                         "owned": owned_map(request.user).get(str(printing.card.uuid), 0)})

    @action(detail=False, methods=["get"], url_path="owned-map")
    def owned_map_view(self, request):
        return Response({"owned": owned_map(request.user)})

    @action(detail=False, methods=["get"])
    def summary(self, request):
        om = owned_map(request.user)
        return Response({
            "distinct_cards": len(om),
            "total_cards": sum(om.values()),
        })


class WishlistView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WishlistSerializer

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related("card").prefetch_related("card__printings")


class WishlistDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, uuid):
        WishlistItem.objects.filter(user=request.user, uuid=uuid).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TradeView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TradeSerializer

    def get_queryset(self):
        return TradeItem.objects.filter(user=self.request.user).select_related("printing__card_set")


class TradeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, uuid):
        TradeItem.objects.filter(user=request.user, uuid=uuid).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
