from collections import Counter

from django.db import transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.constants import (
    AMOUNT_OF_INGREDIENT_CREATE_ERROR, AMOUNT_OF_TAG_CREATE_ERROR,
    AMOUNT_MIN, RECIPES_LIMIT
)
from recipes.models import (
    Ingredient, RecipeIngredients,
    Tag, Recipe, User
)
from .utils import Base64ImageField


class BaseUserSerializer(DjoserUserSerializer):
    """Сериалайзер под текущего пользователя."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            *DjoserUserSerializer.Meta.fields,
            'avatar',
            'is_subscribed',
        )
        read_only_fields = ('id', 'avatar', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return request.user.followers.filter(author=obj).exists()


class AvatarSerializer(serializers.Serializer):
    """Сериалайзер для аватара."""

    avatar = Base64ImageField(required=False)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для короткого отображения рецептов у подписчиков."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriberReadSerializer(BaseUserSerializer):
    """Сериалайзер для подписчиков."""

    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (
            *BaseUserSerializer.Meta.fields, 'recipes', 'recipes_count'
        )
        read_only_fields = fields

    def get_recipes(self, recipe):
        """
        Метод для получения списка рецептов.
        :param obj: объект указанного пользователя.
        :return: сериализованный список рецептов.
        """
        try:
            recipes = recipe.recipes.all()
            recipes_limit = int(self.context.get(
                'request').GET.get('recipes_limit', RECIPES_LIMIT))
            return RecipeShortSerializer(
                recipes[:recipes_limit], many=True).data
        except AttributeError:
            return RecipeShortSerializer(
                recipe.recipes.all()[:RECIPES_LIMIT], many=True).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для Тэгов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для Ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientsSetSerializer(serializers.ModelSerializer):
    """Сериализатор для установки ингредиентов к рецепту."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(
        validators=[
            MinValueValidator(AMOUNT_MIN)
        ]
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
        read_only_fields = fields


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""

    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    author = BaseUserSerializer(read_only=True)
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

    def find_duplicates(self, items, item_name):
        """Метод для поиска дублей в списке и генерации ошибки."""
        # Считаем количество повторений
        item_ids = [item.get('id') if isinstance(
            item, dict) else item for item in items]
        duplicates = [item for item, count in Counter(
            item_ids).items() if count > 1]

        if duplicates:
            raise serializers.ValidationError(
                f"{item_name} {duplicates} дубликаты."
            )

    def validate(self, attrs):
        """Метод для валидации данных при создании рецепта."""
        ingredients = attrs.get('recipe_ingredients')
        tags = attrs.get('tags')
        if not ingredients:
            raise serializers.ValidationError(
                AMOUNT_OF_INGREDIENT_CREATE_ERROR
            )
        if not tags:
            raise serializers.ValidationError(
                AMOUNT_OF_TAG_CREATE_ERROR
            )
        self.find_duplicates(
            [ingredient.get('id') for ingredient in ingredients], "Ingredient")
        self.find_duplicates(tags, "Tag")
        return attrs

    def create_ingredients(self, recipe, ingredients):
        """Метод для создания ингредиентов для рецепта."""
        RecipeIngredients.objects.bulk_create(
                RecipeIngredients(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount']
                ) for ingredient in ingredients
            )

    @transaction.atomic()
    def create(self, validated_data):
        """Метод для создания рецептов."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Метод для обновления рецептов."""
        ingredients = validated_data.pop('recipe_ingredients')
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Метод для представления данных."""
        recipe = super().to_representation(instance)
        recipe.update({
            'tags': TagSerializer(instance.tags.all(), many=True).data,
            'ingredients': RecipeIngredientsGetSerializer(
                instance.recipe_ingredients.all(), many=True
            ).data
        })
        return recipe

    def get_is_favorited(self, favorite):
        request = self.context.get('request')
        return request.user.is_authenticated and favorite.favorites.filter(
            user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return obj.shopping_carts.filter(user=request.user).exists()
        return False
