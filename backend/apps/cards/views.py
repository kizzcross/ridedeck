from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Prefetch, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsPlatformAdminOrReadOnly

from .filters import CardFilter
from .models import Card, CardPrinting, CardSet
from .serializers import (
    CardDetailSerializer,
    CardListSerializer,
    CardSetSerializer,
)


class CardSetViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = CardSet.objects.all()
    serializer_class = CardSetSerializer
    permission_classes = [AllowAny]
    lookup_field = "uuid"
    ordering_fields = ["release_date", "name", "code"]
    search_fields = ["name", "code"]


class CardViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Public, read-only catalog. Writes to cards are admin-only (data corrections)
    and handled through the admin surface, not this endpoint."""

    permission_classes = [IsPlatformAdminOrReadOnly]
    lookup_field = "slug"
    filterset_class = CardFilter
    ordering_fields = ["name", "grade", "power"]

    def get_queryset(self):
        qs = Card.objects.all()
        if self.action == "list":
            qs = qs.prefetch_related(
                Prefetch("printings",
                         queryset=CardPrinting.objects.select_related("card_set").order_by("card_number"),
                         to_attr="prefetched_printings")
            )
        else:
            qs = qs.prefetch_related("printings__card_set", "format_legalities", "external_ids")
        return self._apply_search(qs)

    def _apply_search(self, qs):
        term = self.request.query_params.get("search", "").strip()
        if not term:
            return qs
        # Combined: substring across name/ability + trigram-ranked ordering on name.
        qs = qs.filter(
            Q(name__icontains=term)
            | Q(normalized_name__icontains=term)
            | Q(ability_text__icontains=term)
        )
        return qs.annotate(rank=TrigramSimilarity("name", term)).order_by("-rank", "name")

    def get_serializer_class(self):
        return CardListSerializer if self.action == "list" else CardDetailSerializer

    @extend_schema(parameters=[
        OpenApiParameter("search", str, description="Fuzzy search over name + ability text"),
        OpenApiParameter("grade", str, description="Grade(s), comma-separated"),
        OpenApiParameter("nation", str), OpenApiParameter("clan", str),
        OpenApiParameter("card_type", str), OpenApiParameter("trigger", str),
        OpenApiParameter("format_code", str), OpenApiParameter("set_code", str),
        OpenApiParameter("rarity", str), OpenApiParameter("is_trigger", bool),
    ])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
