from rest_framework import permissions


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """Object-level Tournament Organizer role. A user only manages tournaments
    they organize (or staff / platform admin). Never a global flag."""

    message = "Você não organiza este torneio."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        tournament = getattr(obj, "tournament", obj)
        return tournament.is_organizer(request.user)
