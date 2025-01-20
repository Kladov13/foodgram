from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, RecipeIngredients, Recipe,
                     ShoppingCart, Tag, User)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class UserAdmin(BaseUserAdmin):
    # Список полей для отображения в списке пользователей
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'is_active')

    # Поли для поиска
    search_fields = ('username', 'email')

    # Фильтрация по полям
    list_filter = ('is_staff', 'is_active')

    # Добавьте поля для отображения и редактирования в админке
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
            'fields': ('username', 'password1', 'password2',
                       'email', 'first_name', 'last_name', 'is_staff',
                       'is_active'),
        }),
    )

    # Используем кастомную форму
    form = CustomUserChangeForm

    # Позволяем редактировать пароль через админку
    def get_form(self, request, obj=None, **kwargs):
        if obj:  # Если это уже существующий объект
            kwargs['fields'] = (
                'username', 'email', 'first_name', 'last_name',
                'password', 'is_active', 'is_staff', 'is_superuser')
        return super().get_form(request, obj, **kwargs)


# Регистрируем модель пользователя в админке UserAdmin
admin.site.register(User, UserAdmin)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1
    min_num = 1


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
    list_filter = ('author', 'tags',)
    search_fields = ('name', 'author__username', 'tags__name')
    inlines = [RecipeIngredientInline]
    readonly_fields = ('added_in_favorites',)

    def display_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    display_tags.short_description = 'Теги'

    def display_ingredients(self, obj):
        """Отображает ингредиенты в виде списка."""
        ingredients = obj.ingredients.values_list('name', flat=True)
        return mark_safe("<ul>" + "".join([
            f"<li>{ingredient}</li>" for ingredient in ingredients]) + "</ul>")
    display_ingredients.short_description = "Ингредиенты"

    def display_image(self, obj):
        """Отображает изображение рецепта."""
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" style="max-height: 100px;" />')
        return "Нет изображения"
    display_image.short_description = "Картинка"

    def added_in_favorites(self, obj):
        """Возвращает количество добавлений рецепта в избранное."""
        return obj.favorite_set.count()
    added_in_favorites.short_description = "В избранном"

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

        class CookingTimeFilter(admin.SimpleListFilter):
            title = "Время готовки"
            parameter_name = "cooking_time"

            def lookups(self, request, model_admin):
                return [
                    ('fast', f'''Быстрее {thresholds[0]} мин
                                ({qs.filter(cooking_time__lt=thresholds[0]).count(
                                )})'''),
                    ('medium', f'''Быстрее {thresholds[1]} мин
                                ({qs.filter(cooking_time__range=(
                                    thresholds[0], thresholds[1])).count(
                                )})'''),
                    ('long', f'''Дольше {thresholds[1]} мин
                                ({qs.filter(cooking_time__gt=thresholds[1]).count(
                                )})'''),
                ]

            def queryset(self, request, queryset):
                if self.value() == 'fast':
                    return queryset.filter(cooking_time__lt=thresholds[0])
                if self.value() == 'medium':
                    return queryset.filter(cooking_time__range=(thresholds[0],
                                                                thresholds[1]))
                if self.value() == 'long':
                    return queryset.filter(cooking_time__gt=thresholds[1])
                return queryset

        filters = super().get_list_filter(request)
        return filters + [CookingTimeFilter]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug',)
    search_fields = ('name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(Favorite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe', 'get_favorite_status')

    def get_favorite_status(self, fav):
        return 'В избранном' if fav.favorite else 'Не в избранном'
    get_favorite_status.short_description = 'Статус избранного'


@admin.register(RecipeIngredients)
class IngredientInRecipe(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
