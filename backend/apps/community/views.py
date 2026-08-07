from rest_framework import mixins, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Comment
from .serializers import CommentSerializer


class CommentViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Generic comment thread for any target.

    - ``GET /comments/?target_type=deck&target_uuid=<uuid>`` — thread for one object.
    - ``POST /comments/`` — add a comment (authenticated).
    - ``DELETE /comments/<uuid>/`` — author or platform admin only.
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "uuid"

    def get_queryset(self):
        qs = (
            Comment.objects.filter(deleted_at__isnull=True)
            .select_related("author__profile")
        )
        if self.action == "list":
            tt = self.request.query_params.get("target_type")
            tu = self.request.query_params.get("target_uuid")
            if not (tt and tu):
                return qs.none()
            return qs.filter(target_type=tt, target_uuid=tu)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_destroy(self, instance):
        user = self.request.user
        if instance.author_id != user.id and not user.is_platform_admin:
            raise PermissionDenied("Você não pode remover este comentário.")
        instance.soft_delete()
