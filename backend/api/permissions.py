from djoser.permissions import CurrentUserOrAdminOrReadOnly
from rest_framework.permissions import (
    BasePermission,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS
)

CHANGE_METHODS = ('PUT', 'PATCH', 'DELETE')


class CurrentUserOrAdminOrReadOnly(
    IsAuthenticatedOrReadOnly,
    CurrentUserOrAdminOrReadOnly
):
    pass


class ReadOnly(BasePermission):
    """Доступ к странице только для просмотра."""
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsAuthor(IsAuthenticated):
    """Пермишн для автора."""

    def has_permission(self, request, view):
        return (
            request.method in CHANGE_METHODS
            and super().has_permission(request, view)
        )

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
