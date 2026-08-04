from django.db.models import OuterRef, Subquery
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cards.models import Card
from apps.common.pagination import DefaultPagination
from apps.common.permissions import IsPlatformAdmin

from .models import CardPowerLevel, CardPowerLevelHistory
from .serializers import (
    BulkSetPowerLevelSerializer,
    CardPowerLevelSerializer,
    PowerHistorySerializer,
    SetPowerLevelSerializer,
)
from .services import bulk_set_power_level, default_scale, power_map, set_power_level


class PowerScaleView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        scale = default_scale()
        return Response({
            "min_value": scale.min_value, "max_value": scale.max_value,
            "descriptions": scale.descriptions,
        })


class PublicPowerLevelView(APIView):
    """Public read-only power map for a format."""

    permission_classes = [AllowAny]

    def get(self, request):
        fmt = request.query_params.get("format_code", "standard")
        return Response({"format_code": fmt, "power": power_map(fmt)})


class AdminPowerLevelViewSet(viewsets.GenericViewSet):
    """Platform-Admin-only power level editing (single + bulk) with full audit.

    A normal user or tournament organizer hitting any of these gets 403 —
    enforced here in the backend, never trusting a client flag."""

    permission_classes = [IsPlatformAdmin]
    pagination_class = DefaultPagination

    @extend_schema(request=SetPowerLevelSerializer, responses=CardPowerLevelSerializer)
    @action(detail=False, methods=["post"], url_path="set", url_name="set")
    def set_level(self, request):
        s = SetPowerLevelSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        card = Card.objects.filter(uuid=data["card"]).first()
        if not card:
            return Response({"error": {"code": "not_found", "message": "Carta não encontrada."}},
                            status=status.HTTP_404_NOT_FOUND)
        obj = set_power_level(
            admin=request.user, card=card, format_code=data["format_code"],
            value=data["value"], justification=data["justification"],
            status=data["status"], confidence=data.get("confidence"), tags=data.get("tags"),
        )
        return Response(CardPowerLevelSerializer(obj).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=BulkSetPowerLevelSerializer)
    @action(detail=False, methods=["post"], url_path="bulk", url_name="bulk")
    def bulk_set(self, request):
        s = BulkSetPowerLevelSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        cards = list(Card.objects.filter(uuid__in=data["cards"]))
        results = bulk_set_power_level(
            admin=request.user, cards=cards, format_code=data["format_code"],
            value=data["value"], justification=data["justification"],
        )
        return Response({"updated": len(results), "format_code": data["format_code"],
                         "value": data["value"]}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="cards")
    def cards_with_levels(self, request):
        """Card list annotated with the current power level for a format —
        the backing query for the admin editor. Flags unrated cards."""
        fmt = request.query_params.get("format_code", "standard")
        pl = CardPowerLevel.objects.filter(card=OuterRef("pk"), format_code=fmt)
        qs = Card.objects.annotate(
            power_value=Subquery(pl.values("value")[:1]),
            power_status=Subquery(pl.values("status")[:1]),
        )
        search = request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)
        if request.query_params.get("unrated") == "1":
            qs = qs.filter(power_value__isnull=True)
        qs = qs.order_by("name")
        page = self.paginate_queryset(qs)
        data = [
            {"uuid": str(c.uuid), "name": c.name, "grade": c.grade, "nation": c.nation,
             "clan": c.clan, "image": (c.printings.first().image_url if c.printings.exists() else ""),
             "power_value": c.power_value, "power_status": c.power_status}
            for c in page
        ]
        return self.get_paginated_response(data)

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        card_uuid = request.query_params.get("card")
        fmt = request.query_params.get("format_code", "standard")
        rows = CardPowerLevelHistory.objects.filter(card__uuid=card_uuid, format_code=fmt)
        return Response(PowerHistorySerializer(rows, many=True).data)
