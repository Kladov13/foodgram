from django.contrib.auth.models import AbstractUser
from django.core.validators import (
    MinValueValidator, RegexValidator)
from django.db import models
from django.urls import reverse

from .constants import (
    TAG_NAME_MAX_LENGTH, INGREDIENT_NAME_MAX_LENGTH,
    INGREDIENT_UNIT_MAX_LENGTH, RECIPE_NAME_MAX_LENGTH,
    COOKING_TIME_MIN,
    AMOUNT_MIN,
    EMAIL_MAX_LENGTH, FIO_MAX_FIELD_LENGTH
)


class User(AbstractUser):
    """Кастомный класс для модели User."""

    username = models.CharField(
        'Никнейм',
        max_length=FIO_MAX_FIELD_LENGTH,
        unique=True,
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message=(
                'Логин может содержать только буквы, цифры и символы @/./+/-/_'
            ))])
    email = models.EmailField(max_length=EMAIL_MAX_LENGTH,
                              unique=True,
                              verbose_name='Электронная почта')
    first_name = models.CharField('Имя', max_length=FIO_MAX_FIELD_LENGTH)
    last_name = models.CharField('Фамилия', max_length=FIO_MAX_FIELD_LENGTH)

    # Поле для аватара.
    avatar = models.ImageField(
        upload_to='users/images/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписок."""

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='authors',
        verbose_name='Автор'
    )
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followers',
        verbose_name='Подписчик'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'subscriber'],
                name='unique_follow'
            )
        ]


class Tag(models.Model):
    """Модель для тегов."""

    name = models.CharField(
        verbose_name='Наименование', max_length=TAG_NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Уникальный слаг', max_length=TAG_NAME_MAX_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для ингредиентов."""

    name = models.CharField(
        verbose_name='Наименование',
        max_length=INGREDIENT_NAME_MAX_LENGTH, unique=True
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=INGREDIENT_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель для рецептов."""

    tags = models.ManyToManyField(
        Tag, verbose_name='Тэги'
    )
    author = models.ForeignKey(
        User, verbose_name='Автор', on_delete=models.CASCADE,
        related_name='recipes'
    )
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredients',
        verbose_name='Продукты'
    )
    name = models.CharField(
        verbose_name='Наименование', max_length=RECIPE_NAME_MAX_LENGTH
    )
    image = models.ImageField(
        verbose_name='Изображение', blank=True,
        upload_to='recipes/images/'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                COOKING_TIME_MIN,
            )
        ]
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
        editable=False
    )

    def get_absolute_url(self):
        """Возвращает полный URL для просмотра рецепта."""
        return reverse('recipe-detail', args=[self.id])

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return self.name


class RecipeIngredients(models.Model):
    """Промежуточная модель для связи моделей Рецетов и Ингредиентов."""

    recipe = models.ForeignKey(
        Recipe, verbose_name='Рецепт', on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient, verbose_name='Продукт', on_delete=models.CASCADE
    )
    amount = models.IntegerField(
        verbose_name='Мера',
        validators=[
            MinValueValidator(
                AMOUNT_MIN,
            )
        ]
    )

    class Meta:
        default_related_name = 'recipe_ingredients'
        verbose_name = 'Продукт рецепта'
        verbose_name_plural = 'Продукты рецептов'


class BaseUserRecipe(models.Model):
    """Базовый класс для хранения пользователя и рецепта."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        # Уникальность пары (пользователь + рецепт)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'], name='unique_user_%(class)s'
            )
        ]
        default_related_name = '%(class)ss'
        verbose_name = 'Рецепт пользователя'
        verbose_name_plural = 'Рецепты пользователей'

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в {self._meta.verbose_name}'


class ShoppingCart(BaseUserRecipe):
    """Модель для списка покупок."""

    class Meta(BaseUserRecipe.Meta):

        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'


class Favorite(BaseUserRecipe):
    """Модель для Избранных рецептов."""

    class Meta(BaseUserRecipe.Meta):

        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
