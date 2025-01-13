from django.contrib.auth import get_user_model
from django_filters import rest_framework as filters
from rest_framework.filters import BaseFilterBackend

from recipes.models import Recipe

User = get_user_model()


class IngredientFilter(BaseFilterBackend):
    """Фильтр для Ингредиентов."""

    def filter_queryset(self, request, queryset, view):
        """Метод для поиска рецептов по указанному имени."""
        if 'name' in request.query_params:
            queryset = queryset.filter(
                name__startswith=request.query_params['name']
            )
        return queryset


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    tags = filters.CharFilter(method='filter_tags')
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author',)

    def filter_tags(self, queryset, name, value):
        tags = self.request.query_params.getlist('tags')
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        if not value and user.is_authenticated:
            return queryset.exclude(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset
