from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, RecipeIngredients, Recipe,
                     ShoppingCart, Tag, User)


class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class RelatedObjectFilter(admin.SimpleListFilter):
    """
    Фильтр для проверки наличия связанных объектов.
    Рецепты, подписки, подписчики.
    """

    parameter_name = ''
    related_field_name = ''

    def lookups(self, request, model_admin):
        # Определение возможных значений фильтра
        return [
            ('1', 'Есть'),
            ('0', 'Нет'),
        ]

    def queryset(self, request, queryset):
        # Условие фильтрации на основе текущего значения фильтра
        filter_value = self.value()
        if filter_value == '1':
            return queryset.filter(**{
                f'{self.related_field_name}__isnull': False}).distinct()
        elif filter_value == '0':
            return queryset.filter(**{
                f'{self.related_field_name}__isnull': True}).distinct()
        return queryset


class HasRecipesFilter(RelatedObjectFilter):
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'
    related_field_name = 'recipes'


class HasSubscriptionsFilter(RelatedObjectFilter):
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'
    related_field_name = 'subscriptions'


class HasFollowersFilter(RelatedObjectFilter):
    title = 'Есть подписчики'
    parameter_name = 'has_followers'
    related_field_name = 'followers'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Список полей для отображения в списке пользователей
    list_display = (
        'username', 'email', 'full_name', 'avatar', 'recipe_count',
        'subscription_count', 'follower_count', 'is_staff', 'is_active'
    )

    # Фильтрация по полям
    list_filter = ('is_staff', 'is_active', HasRecipesFilter,
                   HasSubscriptionsFilter, HasFollowersFilter)

    # Поли для поиска
    search_fields = ('username', 'email')

    # Настроенные поля для отображения и редактирования в админке
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                    'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Определяем, какие поля отображать при создании нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email',
                       'first_name', 'last_name', 'is_staff', 'is_active'),
        }),
    )

    form = UserChangeForm

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар')
    @mark_safe
    def avatar(self, user):
        return (
            f'<img src="{user.avatar.url}" style="max-height: 50px; '
            f'max-width: 50px;" />' if user.avatar else "")

    @admin.display(description='Рецепты')
    def recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписки')
    def subscription_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчики')
    def follower_count(self, user):
        return user.followers.count()


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1
    min_num = 1


class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время готовки"
    parameter_name = "cooking_time"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        times = self.model.objects.all().values_list('cooking_time', flat=True)
        if times:
            min_time, max_time = min(times), max(times)
            bin_size = (max_time - min_time) // 3 or 1
            self.thresholds = [
                min_time + bin_size, min_time + 2 * bin_size, max_time]

    def lookups(self, request, model_admin):
        thresholds = self.thresholds
        return [
            ('fast', f'Меньше {thresholds[2][0]} мин'),
            ('medium', f'От {thresholds[2][0]} до {thresholds[6][0]} мин'),
            ('long', f'Больше {thresholds[6][0]} мин'),
        ]

    def filter_by_range(self, queryset, time_range):
        """Фильтрует queryset по переданному диапазону через __range."""
        return queryset.filter(cooking_time__range=time_range)

    def queryset(self, request, queryset):
        if self.value() == 'fast':
            return self.filter_by_range(queryset, self.thresholds[0])
        if self.value() == 'medium':
            return self.filter_by_range(queryset, self.thresholds[1])
        if self.value() == 'long':
            return self.filter_by_range(queryset, self.thresholds[2])
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'display_tags',
        'added_in_favorites',
        'display_ingredients',
        'display_image')

    list_filter = (CookingTimeFilter, 'author', 'tags')
    search_fields = ('name', 'author__username', 'tags__name')
    inlines = [RecipeIngredientInline]

    @admin.display(description='Теги')
    def display_tags(self, obj):
        return '<br>'.join(tag.name for tag in obj.tags.all())

    @admin.display(description='Продукты')
    @mark_safe
    def display_ingredients(self, ingredient):
        """Отображает ингредиенты в виде списка."""
        ingredients = ingredient.recipe_ingredients.all()
        return '<br>'.join(
            f'{item}'
            for item in ingredients)

    @admin.display(description='Картинка')
    @mark_safe
    def display_image(self, recipe):
        """Отображает изображение рецепта, если оно существует."""
        return (
            f'<img src="{recipe.image.url}" style="max-height: 100px;" />'
            if recipe.image else ''
        )

    @admin.display(description='В избранном')
    def added_in_favorites(self, recipe):
        """Возвращает количество добавлений рецепта в избранное."""
        return Favorite.objects.filter(recipe=recipe).count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @admin.display(description='Рецепты')
    def recipe_count(self, ingredient):
        """Показывает количество рецептов, в которых используется ингредиент"""
        return RecipeIngredients.objects.filter(ingredient=ingredient).count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug')

    @admin.display(description='Рецепты')
    def recipe_count(self, tag):
        """Показывает количество рецептов, с этим тегом."""
        return tag.recipe_set.count()


@admin.register(ShoppingCart, Favorite)
class FavouriteAndShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(RecipeIngredients)
class IngredientInRecipe(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
