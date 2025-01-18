from django.contrib import admin

from .models import (Favorite, Ingredient, RecipeIngredients, Recipe,
                     ShoppingCart, Tag)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from .models import User  # Импортируйте вашу модель пользователя

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

class UserAdmin(BaseUserAdmin):
    # Список полей для отображения в списке пользователей
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')

    # Поли для поиска
    search_fields = ('username', 'email')

    # Фильтрация по полям
    list_filter = ('is_staff', 'is_active')

    # Добавьте поля для отображения и редактирования в админке
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Определяем, какие поля отображать при создании нового пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email', 'first_name', 'last_name', 'is_staff', 'is_active'),
        }),
    )

    # Используем нашу кастомную форму
    form = CustomUserChangeForm

    # Позволяем редактировать пароль через админку
    def get_form(self, request, obj=None, **kwargs):
        if obj:  # Если это уже существующий объект
            kwargs['fields'] = ('username', 'email', 'first_name', 'last_name', 'password', 'is_active', 'is_staff', 'is_superuser')
        return super().get_form(request, obj, **kwargs)

# Регистрируем модель пользователя в админке с нашим UserAdmin
admin.site.register(User, UserAdmin)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredients
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'added_in_favorites')
    search_fields = ('name', 'author__username', 'tags__name')
    inlines = [RecipeIngredientInline]

    @admin.display(description='Число добавлений в избранное рецепта')
    def added_in_favorites(self, obj):
        return obj.favorites.count()


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
    list_display = ('user', 'recipe',)


@admin.register(RecipeIngredients)
class IngredientInRecipe(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount',)
