from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
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
        ('1', _('Есть')),
        ('0', _('Нет')),
    ]
    
    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(**{f'{self.related_field_name}__isnull': False}).distinct()
        if self.value() == '0':
            return queryset.filter(**{f'{self.related_field_name}__isnull': True}).distinct()
        return queryset


class HasRecipesFilter(RelatedObjectFilter):
    title = _('Есть рецепты')
    parameter_name = 'has_recipes'
    related_field_name = 'recipes'


class HasSubscriptionsFilter(RelatedObjectFilter):
    title = _('Есть подписки')
    parameter_name = 'has_subscriptions'
    related_field_name = 'subscriptions'  # Убедитесь, что в модели User есть related_name для подписок


class HasFollowersFilter(RelatedObjectFilter):
    title = _('Есть подписчики')
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
        (_('Персональная информация'), {'fields': (
            'first_name', 'last_name', 'email', 'avatar'
        )}),
        (_('Права'), {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        (_('Важные даты'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email',
                       'first_name', 'last_name', 'is_staff', 'is_active'),
        }),
    )
    form = UserChangeForm

    @admin.display(description=_('ФИО'))
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description=_('Аватар'))
    def avatar_preview(self, user):
        if user.avatar:
            return mark_safe(f'<img src="{user.avatar.url}" style="max-height: 50px; max-width: 50px;" />')
        return _("Нет аватара")

    @admin.display(description=_('Рецепты'))
    def recipe_count(self, user):
        return user.recipes.count()

    @admin.display(description=_('Подписки'))
    def subscription_count(self, user):
        return user.followers.count()

    @admin.display(description=_('Подписчики'))
    def follower_count(self, user):
        return user.authors.count()

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'author')
    search_fields = (
        'subscriber__username',
        'author__username',
        'subscriber__email',
        'author__email'
    )

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1
    min_num = 1


class CookingTimeFilter(admin.SimpleListFilter):
    title = _("Время (мин)")
    parameter_name = "cooking_time"

    def lookups(self, request, model_admin):
        return [
            ('0-30', _('До 30 мин')),
            ('30-60', _('30-60 мин')),
            ('60+', _('Более 60 мин')),
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
        'tags_display', 'added_in_favorites', 'ingredients_list', 'image_preview'
    )
    list_filter = (CookingTimeFilter, 'author', 'tags')
    search_fields = ('name', 'author__username', 'tags__name')
    inlines = [RecipeIngredientInline]
    verbose_name = _('Рецепт')
    verbose_name_plural = _('Рецепты')

    @admin.display(description=_('Теги'))
    def tags_display(self, obj):
        return ", ".join(tag.name for tag in obj.tags.all())

    @admin.display(description=_('Продукты'))
    def ingredients_list(self, obj):
        return ", ".join(
            f"{ing.ingredient.name} ({ing.amount} {ing.ingredient.measurement_unit})"
            for ing in obj.recipe_ingredients.all()
        )

    @admin.display(description=_('Изображение'))
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px;" />')
        return _("Нет изображения")

    @admin.display(description=_('В избранном'))
    def added_in_favorites(self, obj):
        return obj.favorites.count()

    @admin.display(description=_('Время (мин)'))
    def cooking_time_display(self, obj):
        return obj.cooking_time


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'recipe_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @admin.display(description=_('Рецептов'))
    def recipe_count(self, obj):
        return obj.recipes.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'recipe_count')
    search_fields = ('name', 'slug')

    @admin.display(description=_('Рецептов'))
    def recipe_count(self, obj):
        return obj.recipes.count()


@admin.register(ShoppingCart, Favorite)
class FavouriteAndShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(RecipeIngredients)
class IngredientInRecipe(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
