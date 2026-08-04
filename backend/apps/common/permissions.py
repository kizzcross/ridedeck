"""Reusable DRF permission classes.

The golden rule of this platform: permission checks live in the backend and are
never trusted from client-supplied flags.
"""
from rest_framework import permissions


class IsPlatformAdmin(permissions.BasePermission):
    """Only the global Platform Admin. Guards power level, official banlists,
    format rules, catalog sync — the editorial/authoritative surface."""

    message = "Only a Platform Admin may perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_platform_admin)


class IsPlatformAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_platform_admin)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level: only the owner may mutate; reads follow view rules.

    The owning attribute is configurable via ``owner_field`` on the view
    (defaults to ``owner``)."""

    message = "You do not own this object."

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner_field = getattr(view, "owner_field", "owner")
        owner = getattr(obj, owner_field, None)
        return owner == request.user or request.user.is_platform_admin


class IsAuthenticatedOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    pass
