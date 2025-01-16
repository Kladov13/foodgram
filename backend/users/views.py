from django.shortcuts import get_object_or_404
from djoser import views as djoser_views
from djoser.permissions import CurrentUserOrAdmin
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .constants import (
    CHANGE_AVATAR_ERROR_MESSAGE, SUBSCRIBE_ERROR_MESSAGE,
    SUBSCRIBE_DELETE_ERROR_MESSAGE, SUBSCRIBE_SELF_ERROR_MESSAGE
)
from .models import Subscription, User
from .serializers import (
    AvatarSerializer,
    SubscriptionGetSerializer,
    SubscriptionEditSerializer,
    UserSerializer
)


class UserViewSet(djoser_views.UserViewSet):
    """Общий вьюсет для пользователя."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination
    pagination_class.page_size_query_param = 'limit'

    @action(
        ["get", "put", "patch", "delete"],
        detail=False,
        permission_classes=[CurrentUserOrAdmin]
    )
    def me(self, request, *args, **kwargs):
        """Метод для профиля."""
        return super().me(request, *args, **kwargs)

    @action(
        ['PUT', 'DELETE'],
        detail=False,
        url_path='me/avatar'
    )
    def change_avatar(self, request, *args, **kwargs):
        """Метод для управления аватаром."""
        if request.method == 'DELETE':
            self.request.user.avatar = None
            self.request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if 'avatar' not in request.data:
            return Response(
                {'avatar': CHANGE_AVATAR_ERROR_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar_data = serializer.validated_data.get('avatar')
        request.user.avatar = avatar_data
        request.user.save()
        image_url = request.build_absolute_uri(
            f'/media/users/{avatar_data.name}'
        )
        return Response(
            {'avatar': str(image_url)}, status=status.HTTP_200_OK
        )

    @action(['GET'], detail=False, url_path='subscriptions')
    def subscriptions(self, request):
        """Метод для управления подписками пользователя."""
        user = request.user
        queryset = User.objects.filter(followings__follower=user)
        pages = self.paginate_queryset(queryset)
        self.serializer_class = SubscriptionGetSerializer
        serializer = self.get_serializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('POST', 'DELETE'),
        url_path='subscribe',
        url_name='subscribe',
    )
    def subscribe(self, request, id):
        """Метод для управления редактирования подписок."""
        user = request.user
        author = get_object_or_404(User, id=id)
        serializer = SubscriptionEditSerializer(
            data={'followed': author.id, 'follower': user.id}
        )
        if request.method == 'POST':
            # Проверка подписки на самого себя.
            if user == author:
                return Response(
                    {'error': SUBSCRIBE_SELF_ERROR_MESSAGE},
                    status=status.HTTP_400_BAD_REQUEST)
            # Проверка уже существующей подписки.
            elif Subscription.objects.filter(
                    followed=author, follower=user).exists():
                return Response(
                    {'error': SUBSCRIBE_ERROR_MESSAGE},
                    status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )

        if Subscription.objects.filter(
                followed=author, follower=user).exists():
            subscription = Subscription.objects.get(
                followed=author, follower=user)
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'errors': SUBSCRIBE_DELETE_ERROR_MESSAGE},
                status=status.HTTP_400_BAD_REQUEST)
