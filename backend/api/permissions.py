from rest_framework.permissions import IsAuthenticated


class IsAuthor(IsAuthenticated):
    """Пермишн для автора."""

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
