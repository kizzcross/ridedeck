from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from .models import GameFormat
from .serializers import GameFormatSerializer


class GameFormatViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = GameFormat.objects.filter(is_active=True)
    serializer_class = GameFormatSerializer
    permission_classes = [AllowAny]
    lookup_field = "code"
