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
    # Словарь для условий фильтрации
    LOOKUPS = {
        '1': {f'{related_field_name}__isnull': False},
        '0': {f'{related_field_name}__isnull': True},
    }

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def queryset(self, request, queryset):
        filter_condition = self.LOOKUPS.get(self.value())
        if filter_condition:
            return queryset.filter(**filter_condition).distinct()
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
            f'max-width: 50px;" />' if user.avatar else "<i>Нет картинки</i>")

    @admin.display(description='Рецепты')
    def recipe_count(self, recipe):
        return recipe.recipes.count()

    @admin.display(description='Подписки')
    def subscription_count(self, obj):
        return obj.subscriptions.count()

    @admin.display(description='Подписчики')
    def follower_count(self, obj):
        return obj.followers.count()


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1
    min_num = 1


class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время готовки"
    parameter_name = "cooking_time"
    thresholds = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = self.model.objects.all()
        times = qs.values_list('cooking_time', flat=True)
        if times:
            min_time, max_time = min(times), max(times)
            bin_size = (max_time - min_time) // 3 or 1
            self.thrs = [
                min_time + bin_size, min_time + 2 * bin_size, max_time]
        else:
            self.thrs = [10, 30, 60]

    def filter_by_range(self, queryset, value, thrs):
        """Фильтрует queryset по значению и порогам через __range."""
        filter_mapping = {
            'fast': {'cooking_time__lt': thrs[0]},
            'medium': {'cooking_time__range': (thrs[0], thrs[1])},
            'long': {'cooking_time__gt': thrs[1]},
        }
        # Получаем фильтр из словаря, если value соответствует ключу
        filter_criteria = filter_mapping.get(value)
        # Если фильтр найден, применяем его
        if filter_criteria:
            return queryset.filter(**filter_criteria)
        # Если нет подходящего значения, возвращаем queryset без изменений
        return queryset

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        self.set_thresholds(qs)
        thresholds = self.thresholds
        filter = self.filter_by_range

        return [
            (
                'fast',
                f'Быстрее {thresholds[0]} мин ',
                f'({filter(qs, "ing_time", [thresholds[0]]).count()})',
            ),
            (
                'medium',
                f'Быстрее {thresholds[1]} мин ',
                f'({filter(qs, "cooking_time", thresholds[:2]).count()})',
            ),
            (
                'long',
                f'Дольше {thresholds[1]} мин ',
                f'({filter(qs, "cooking_time", [thresholds[1]]).count()})',
            ),
        ]

    def queryset(self, request, queryset):
        thresholds = self.get_thresholds(request)
        if self.value():
            return self.filter_by_range(queryset, self.value(), thresholds)
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
    def display_ingredients(self, product):
        """Отображает ингредиенты в виде списка."""
        ingredients = product.ingredients.all()
        return '<br>'.join(
            f'{item.ingredient.name} — {item.amount} {item.ingredient.unit}'
            for item in ingredients)

    @admin.display(description='Картинка')
    @mark_safe
    def display_image(self, img):
        """Отображает изображение рецепта, если оно существует."""
        return (
            f'<img src="{img.image.url}" style="max-height: 100px;" />'
            if img.image else ''
        )

    @admin.display(description='В избранном')
    def added_in_favorites(self, fav):
        """Возвращает количество добавлений рецепта в избранное."""
        return fav.favorite_set.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @admin.display(description='Рецепты')
    def recipe_count(self, recipe):
        """Показывает количество рецептов, в которых используется ингредиент"""
        return recipe.recipe_set.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug')

    @admin.display(description='Рецепты')
    def recipe_count(self, recipe):
        """Показывает количество рецептов, с этим тегом."""
        return recipe.recipe_set.count()


@admin.register(ShoppingCart, Favorite)
class FavouriteAndShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(RecipeIngredients)
class IngredientInRecipe(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
