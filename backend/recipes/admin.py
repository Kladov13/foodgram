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
        return [
            ('1', f'Есть {self.related_field_name}'),
            ('0', f'Нет {self.related_field_name}'),
        ]

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(
                **{f'{self.related_field_name}__isnull': False}).distinct()
        if self.value() == '0':
            return queryset.filter(
                **{f'{self.related_field_name}__isnull': True})
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

    # Позволяем редактировать пароль через админку
    def get_form(self, request, obj=None, **kwargs):
        if obj:  # Если это уже существующий объект
            kwargs['fields'] = (
                'username', 'email', 'first_name', 'last_name', 'password',
                'is_active', 'is_staff', 'is_superuser'
            )
        return super().get_form(request, obj, **kwargs)

    @admin.display(description='ФИО')
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    @admin.display(description='Аватар')
    @mark_safe
    def avatar(self, obj):
        return (
            f'<img src="{obj.avatar.url}" style="max-height: 50px; '
            f'max-width: 50px;" />' if obj.avatar else "<i>Нет картинки</i>")

    @admin.display(description='Число рецептов')
    def recipe_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Число подписок')
    def subscription_count(self, obj):
        return obj.subscriptions.count()

    @admin.display(description='Число подписчиков')
    def follower_count(self, obj):
        return obj.followers.count()

    @admin.display(description='Есть рецепты')
    def has_recipes(self, obj):
        return obj.recipes.exists()

    @admin.display(description='Есть подписки')
    def has_subscriptions(self, obj):
        return obj.subscriptions.exists()

    @admin.display(description='Есть подписчики')
    def has_followers(self, obj):
        return obj.followers.exists()


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1
    min_num = 1


class CookingTimeFilter(admin.SimpleListFilter):
    title = "Время готовки"
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        qs = model_admin.get_queryset(request)
        times = qs.values_list('cooking_time', flat=True)

        if times:
            min_time, max_time = min(times), max(times)
            bin_size = (max_time - min_time) // 3 or 1
            thresholds = [
                min_time + bin_size, min_time + 2 * bin_size, max_time
            ]
        else:
            thresholds = [10, 30, 60]  # Дефолтные пороги

        return [
        (
            'fast', f'Быстрее {thresholds[0]} мин '
                    f'({qs.filter(cooking_time__lt=thresholds[0]).count()})'),
            (
            'medium', f'Быстрее {thresholds[1]} мин '
                      f'({qs.filter(cooking_time__range=(thresholds[0], thresholds[1])).count()})'),
            (
            'long', f'Дольше {thresholds[1]} мин '
                    f'({qs.filter(cooking_time__gt=thresholds[1]).count()})'),
        ]

    def queryset(self, request, queryset):
        thresholds = self.get_thresholds(request)
        if self.value():
            return self.filter_by_range(queryset, self.value(), thresholds)
        return queryset

    def get_thresholds(self, request):
        qs = self.model.objects.all()
        times = qs.values_list('cooking_time', flat=True)
        if times:
            min_time, max_time = min(times), max(times)
            bin_size = (max_time - min_time) // 3 or 1
            return [min_time + bin_size, min_time + 2 * bin_size, max_time]
        return [10, 30, 60]

    def filter_by_range(self, queryset, value, thresholds):
        """Фильтрует queryset по значению и порогам через __range."""
        if value == 'fast':
            return queryset.filter(cooking_time__lt=thresholds[0])
        if value == 'medium':
            return queryset.filter(
                cooking_time__range=(thresholds[0], thresholds[1]))
        if value == 'long':
            return queryset.filter(cooking_time__gt=thresholds[1])
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

    list_filter = (CookingTimeFilter,)
    search_fields = ('name', 'author__username', 'tags__name')
    inlines = [RecipeIngredientInline]

    @admin.display(description='Теги')
    def display_tags(self, obj):
        return "\n".join(tag.name for tag in obj.tags.all())

    @admin.display(description='Ингридиенты')
    def display_ingredients(self, obj):
        """Отображает ингредиенты в виде списка."""
        ingredients = obj.ingredients.all()
        return mark_safe("<br>".join(
            f"{ingredient.name} ({ingredient.unit}) — {ingredient.amount}"
            for ingredient in ingredients))

    @admin.display(description='Картинка')
    def display_image(self, obj):
        """Отображает изображение рецепта."""
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="max-height: 100px;" />')
        return ''

    @admin.display(description='В избранном')
    def added_in_favorites(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorite_set.count()

    def get_list_filter(self, request):
        """Добавляем фильтр по времени готовки с динамическими порогами."""
        qs = self.get_queryset(request)
        times = qs.values_list('cooking_time', flat=True)

        if times:
            min_time, max_time = min(times), max(times)
            bin_size = (max_time - min_time) // 3 or 1
            thresholds = [
                min_time + bin_size, min_time + 2 * bin_size, max_time]
        else:
            thresholds = [10, 30, 60]  # Дефолтные пороги


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @admin.display(description='Число рецептов')
    def recipe_count(self, obj):
        """Показывает количество рецептов, в которых используется ингредиент."""
        return obj.recipe_set.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug')

    @admin.display(description='Число рецептов')
    def recipe_count(self, obj):
        """Показывает количество рецептов, с этим тегом."""
        return obj.recipe_set.count()


@admin.register(ShoppingCart, Favorite)
class FavouriteAndShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(RecipeIngredients)
class IngredientInRecipe(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
