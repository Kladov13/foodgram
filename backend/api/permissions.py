from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from djoser.permissions import CurrentUserOrAdminOrReadOnly

class CurrentUserOrAdminOrReadOnly( 
    IsAuthenticatedOrReadOnly, 
    CurrentUserOrAdminOrReadOnly 
): 
    pass

class IsAuthor(IsAuthenticated):
    """Пермишн для автора."""

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
