from django.db import transaction
from rest_framework import serializers

from .constants import (
    AMOUNT_OF_INGREDIENT_CREATE_ERROR, AMOUNT_OF_TAG_CREATE_ERROR,
    DUPLICATE_OF_INGREDIENT_CREATE_ERROR, DUPLICATE_OF_TAG_CREATE_ERROR,
)
from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredients,
    Tag
)

from .utils import Base64ImageField
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.models import Recipe, User, Subscription
from .constants import RECIPES_LIMIT


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

class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для Тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для Ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class RecipeIngredientsSetSerializer(serializers.ModelSerializer):
    """Сериализатор для установки ингредиентов к рецепту."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount')


class RecipeIngredientsGetSerializer(serializers.ModelSerializer):
    """Сериализатор для получения ингредиентов."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""

    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientsSetSerializer(
        many=True,
        source='recipe_ingredients',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'image', 'is_favorited',
            'is_in_shopping_cart', 'name', 'text', 'cooking_time'
        )

    def validate(self, attrs):
        """Метод для валидации данных при создании рецепта."""
        ingredients = attrs.get('recipe_ingredients')
        tags = attrs.get('tags')
        if not ingredients or not tags:
            raise serializers.ValidationError(
                AMOUNT_OF_INGREDIENT_CREATE_ERROR
            )
        if not tags:
            raise serializers.ValidationError(
                AMOUNT_OF_TAG_CREATE_ERROR
            )
        set_ingredients = set(
            ingredient.get('id') for ingredient in ingredients
        )
        set_tags = set(tags)
        if len(ingredients) != len(set_ingredients):
            raise serializers.ValidationError(
                DUPLICATE_OF_INGREDIENT_CREATE_ERROR
            )
        if len(tags) != len(set_tags):
            raise serializers.ValidationError(
                DUPLICATE_OF_TAG_CREATE_ERROR
            )

        return attrs

    def create_ingredients(self, recipe, ingredients):
        """Метод для создания ингредиентов для рецепта."""
        ingredients_qs = [
            RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
        RecipeIngredients.objects.bulk_create(ingredients_qs)

    def check_duplicate_ingredients(self, ingredients):
        """Метод для проверки наличия дубликатов ингредиентов."""
        existing_ingredients = set(
            RecipeIngredients.objects.values_list('ingredient', flat=True)
        )
        for ingredient in ingredients:
            base_ingredient = ingredient.get('id')
            if base_ingredient in existing_ingredients:
                raise serializers.ValidationError(
                    {'errors': DUPLICATE_OF_INGREDIENT_CREATE_ERROR}
                )

    @transaction.atomic()
    def create(self, validated_data):
        """Метод для создания рецептов."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Метод для обновления рецептов."""
        ingredients = validated_data.pop('recipe_ingredients')
        super().update(instance, validated_data)
        self.check_duplicate_ingredients(ingredients)
        self.create_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        """Метод для представления данных."""
        recipe = super().to_representation(instance)
        recipe['tags'] = TagSerializer(
            instance.tags.all(), many=True
        ).data
        recipe['ingredients'] = RecipeIngredientsGetSerializer(
            instance.recipe_ingredients.all(), many=True
        ).data
        return recipe

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return obj.favorites.filter(user=request.user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return obj.shopping_cart.filter(user=request.user).exists()
        return False


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериалайзер для добавления рецепта в список покупок."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
