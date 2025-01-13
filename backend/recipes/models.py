from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from api.constants import (
    TAG_NAME_MAX_LENGTH, INGREDIENT_NAME_MAX_LENGTH,
    INGREDIENT_UNIT_MAX_LENGTH, RECIPE_NAME_MAX_LENGTH,
    COOKING_TIME_MIN_VALUE, COOKING_TIME_ERROR_MESSAGE,
    AMOUNT_OF_INGREDIENT_MIN_VALUE,
    AMOUNT_OF_INGREDIENT_MIN_VALUE_ERROR_MESSAGE, MAX_LENGTH_SHORT_LINK
)
from .utils import generate_short_link


User = get_user_model()


class Tag(models.Model):
    """Модель для тегов."""

    tag_slugs = (
        ('завтрак', 'breakfast'),
        ('обед', 'lunch'),
        ('ужин', 'dinner')
    )

    name = models.CharField(
        verbose_name='Наименование тега', max_length=TAG_NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Уникальный слаг', max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        choices=tag_slugs
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tag'
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']


class Ingredient(models.Model):
    """Модель для ингредиентов."""

    name = models.CharField(
        verbose_name='Наименование ингредиента',
        max_length=INGREDIENT_NAME_MAX_LENGTH, unique=True
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=INGREDIENT_UNIT_MAX_LENGTH
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ingredient'
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']


class Recipe(models.Model):
    """Модель для рецептов."""

    tags = models.ManyToManyField(
        Tag, through='RecipeTags', verbose_name='Тэги рецепта'
    )
    author = models.ForeignKey(
        User, verbose_name='Автор рецепта', on_delete=models.CASCADE
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredients',
        verbose_name='Ингредиенты рецепта'
    )
    name = models.CharField(
        verbose_name='Наименование рецепта', max_length=RECIPE_NAME_MAX_LENGTH
    )
    image = models.ImageField(
        verbose_name='Путь до картинки', blank=True,
        upload_to='recipes/images/'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                COOKING_TIME_MIN_VALUE,
                message=COOKING_TIME_ERROR_MESSAGE),
        ]
    )
    short_link = models.CharField(
        verbose_name='Короткая ссылка', default=generate_short_link,
        max_length=MAX_LENGTH_SHORT_LINK
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self) -> str:
        return f'/recipes/{self.pk}/'

    class Meta:
        db_table = 'recipe'
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['name']


class RecipeTags(models.Model):
    """Промежуточная модель для связи моделей Рецетов и Тэгов."""

    recipe = models.ForeignKey(
        Recipe, verbose_name='Рецепт', on_delete=models.CASCADE
    )
    tag = models.ForeignKey(
        Tag, verbose_name='Тег', on_delete=models.CASCADE
    )

    class Meta:
        db_table = 'recipe_tags'
        default_related_name = 'recipe_tags'
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'


class RecipeIngredients(models.Model):
    """Промежуточная модель для связи моделей Рецетов и Ингредиентов."""

    recipe = models.ForeignKey(
        Recipe, verbose_name='Рецепт', on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient, verbose_name='Ингредиент', on_delete=models.CASCADE
    )
    amount = models.IntegerField(
        verbose_name='Количество в рецепте',
        validators=[
            MinValueValidator(
                AMOUNT_OF_INGREDIENT_MIN_VALUE,
                message=AMOUNT_OF_INGREDIENT_MIN_VALUE_ERROR_MESSAGE),
        ]
    )

    class Meta:
        db_table = 'recipe_ingredients'
        default_related_name = 'recipe_ingredients'
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'


class ShoppingCart(models.Model):
    """Модель для списка покупок."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор списка покупок.',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        db_table = 'shopping_cart'
        default_related_name = 'shopping_cart'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в список покупок.'


class Favorite(models.Model):
    """ Модель для Избранных рецептов."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
    )

    class Meta:
        db_table = 'favorites'
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_favourite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил "{self.recipe}" в Избранное'