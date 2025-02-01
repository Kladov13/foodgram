from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.contrib.auth.models import Group

from .models import (Favorite, Ingredient, RecipeIngredients, Recipe,
                     ShoppingCart, Tag, User, Subscription)

# Убираем стандартные модели
admin.site.unregister(Group)


class RelatedObjectFilter(admin.SimpleListFilter):
    """
    Фильтр для проверки наличия связанных объектов.
    Рецепты, подписки, подписчики.
    """
    parameter_name = ''
    related_field_name = ''
    LOOKUP_CHOICES = [
        ('1', ('Есть')),
        ('0', ('Нет')),
    ]

    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(**{
                f'{self.related_field_name}__isnull': False}).distinct()
        if self.value() == '0':
            return queryset.filter(**{
                f'{self.related_field_name}__isnull': True}).distinct()
        return queryset


class HasRecipesFilter(RelatedObjectFilter):
    title = ('Есть рецепты')
    parameter_name = 'has_recipes'
    related_field_name = 'recipes'


class HasSubscriptionsFilter(RelatedObjectFilter):
    title = ('Есть подписки')
    parameter_name = 'has_subscriptions'
    related_field_name = 'authors'


class HasFollowersFilter(RelatedObjectFilter):
    title = ('Есть подписчики')
    parameter_name = 'has_followers'
    related_field_name = 'followers'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'full_name', 'avatar_preview',
        'recipe_count', 'subscription_count', 'follower_count'
    )
    list_filter = (
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasFollowersFilter,
    )
    search_fields = ('username', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Персональная информация'), {'fields': (
            'first_name', 'last_name', 'email', 'avatar'
        )}),
        (('Права'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (('Важные даты'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email',
                       'first_name', 'last_name', 'is_staff', 'is_active'),
        }),
    )

    @admin.display(description=('ФИО'))
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description=('Аватар'))
    def avatar_preview(self, user):
        if user.avatar:
            return mark_safe(f'<img src="{user.avatar.url}" '
                             f'style="max-height: 50px; max-width: 50px;" />')
        return ("Нет аватара")

    @admin.display(description=('Рецепты'))
    def recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description=('Подписки'))
    def subscription_count(self, user):
        return user.followers.count()

    @admin.display(description=('Подписчики'))
    def follower_count(self, user):
        return user.authors.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('author', 'subscriber')
    search_fields = (
        'subscriber__username',
        'author__username',
        'subscriber__email',
        'author__email'
    )
    list_filter = ('author', 'subscriber')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1
    min_num = 1
    verbose_name = ('Продукт')
    verbose_name_plural = ('Продукты')
    fields = ('ingredient', 'get_measurement_unit', 'amount')
    readonly_fields = ('get_measurement_unit',)

    @admin.display(description=('Ед. изм.'))
    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit


class CookingTimeFilter(admin.SimpleListFilter):
    title = ("Время (мин)")
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        # Применяем одноразовые переменные для соблюдения PEP8
        light = Recipe.objects.filter(cooking_time__lte=30).count()
        medium = Recipe.objects.filter(
            cooking_time__gt=30, cooking_time__lte=60).count()
        though = Recipe.objects.filter(cooking_time__gt=60).count()
        return [
            ('0-30', f'До 30 мин ({light})'),
            ('30-60', f'30-60 мин ({medium})'),
            ('60+', f'Более 60 мин ({though})'),
        ]

    def queryset(self, request, queryset):
        if self.value() == '0-30':
            return queryset.filter(cooking_time__lte=30)
        if self.value() == '30-60':
            return queryset.filter(cooking_time__gt=30, cooking_time__lte=60)
        if self.value() == '60+':
            return queryset.filter(cooking_time__gt=60)
        return queryset


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'author', 'cooking_time_display',
        'tags_display', 'added_in_favorites',
        'ingredients_list', 'image_preview'
    )
    list_filter = (CookingTimeFilter, 'author', 'tags')
    search_fields = ('name', 'author__username', 'tags__name')
    inlines = [RecipeIngredientInline]
    verbose_name = ('Рецепт')
    verbose_name_plural = ('Рецепты')

    @admin.display(description=('Теги'))
    def tags_display(self, obj):
        return '<br>'.join(tag.name for tag in obj.tags.all())

    @admin.display(description=('Продукты'))
    def ingredients_list(self, obj):
        return mark_safe('<ul>' + ''.join(
            f'<li>{ing.ingredient.name} {ing.amount} '
            f'{ing.ingredient.measurement_unit}</li>'
            for ing in obj.recipe_ingredients.all()) + '</ul>')

    @admin.display(description=('Изображение'))
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="max-height: 50px;" />')
        return ('')

    @admin.display(description=('В избранном'))
    def added_in_favorites(self, obj):
        return obj.favorites.count()

    @admin.display(description=('Время (мин)'))
    def cooking_time_display(self, obj):
        return obj.cooking_time


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @admin.display(description=('Рецептов'))
    def recipe_count(self, obj):
        return obj.recipes.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug')

    @admin.display(description=('Рецептов'))
    def recipe_count(self, obj):
        return obj.recipes.count()


@admin.register(ShoppingCart, Favorite)
class FavouriteAndShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(RecipeIngredients)
class IngredientInRecipe(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
