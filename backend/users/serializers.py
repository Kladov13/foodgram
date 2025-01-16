from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.models import Recipe
from .constants import RECIPES_LIMIT
from .models import Subscription
from .utils import Base64ImageField


# Получение объекта пользователя.
User = get_user_model()


class MeUserSerializer(DjoserUserSerializer):
    """Сериалайзер под текущего пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj):
        return False


class UserSerializer(MeUserSerializer):
    """Общий сериалайзер для пользователя."""

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return Subscription.objects.filter(follower_id=request.user.id,
                                           followed_id=obj.id).exists()


class AvatarSerializer(serializers.Serializer):
    """Сериалайзер для аватара."""

    avatar = Base64ImageField(required=False)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для короткого отображения рецептов у подписчиков."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionGetSerializer(serializers.ModelSerializer):
    """Сериалайзер для подписчиков. Только для чтения."""

    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed')
    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj):
        """
        Метод для проверки - является ли текущий пользователь
        подписчиком указанного пользователя.
        :param obj: объект указанного пользователя.
        :return: возвращает булевое значение, в зависимости от подписки.
        """
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            follower=request.user, followed=obj
        ).exists()

    def get_recipes(self, obj):
        """
        Метод для получения списка рецептов.
        :param obj: объект указанного пользователя.
        :return: сериализованный список рецептов.
        """
        try:
            request = self.context.get('request')
            recipes_limit = request.GET.get('recipes_limit')
        except AttributeError:
            recipes_limit = RECIPES_LIMIT
        queryset = obj.recipes.all()
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        return RecipeShortSerializer(queryset, many=True).data


class SubscriptionEditSerializer(serializers.ModelSerializer):
    """Сериалайзер для подписчиков. Только на запись."""

    followed = UserSerializer
    follower = UserSerializer

    class Meta:
        model = Subscription
        fields = ('followed', 'follower')

    def to_representation(self, instance):
        subscription = super().to_representation(instance)
        subscription = SubscriptionGetSerializer(instance.follower).data
        return subscription
