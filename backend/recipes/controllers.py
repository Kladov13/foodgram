from django.shortcuts import get_object_or_404, redirect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Subscription, User, Recipe


@api_view(['POST', 'DELETE'])
def manage_subscription(request, user_id):
    """Обрабатывает подписку (создание/удаление) для пользователя."""

    # Получаем текущего пользователя
    user = request.user

    # Получаем пользователя, на которого осуществляется подписка
    followed_user = get_object_or_404(User, id=user_id)

    # В зависимости от метода (POST для подписки, DELETE для отписки)
    if request.method == 'POST':
        # Проверяем, не подписан ли уже пользователь
        if Subscription.objects.filter(follower=user,
                                       followed=followed_user).exists():
            return Response({"detail": "You are already subscribed."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Создаем подписку
        Subscription.objects.create(follower=user, followed=followed_user)
        return Response({"detail": "Successfully subscribed."},
                        status=status.HTTP_201_CREATED)

    elif request.method == 'DELETE':
        # Удаляем подписку
        subscription = get_object_or_404(Subscription, follower=user,
                                         followed=followed_user)
        subscription.delete()
        return Response({"detail": "Successfully unsubscribed."},
                        status=status.HTTP_204_NO_CONTENT)


def recipe_redirect(request, short_link):
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return redirect(recipe.get_absolute_url())
