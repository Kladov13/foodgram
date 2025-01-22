from django_filters import rest_framework as filters
from rest_framework.filters import BaseFilterBackend

from recipes.models import Recipe, User


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

    def filter_tags(self, recipes, name, value):
        tags = self.request.query_params.getlist('tags')
        if tags:
            return recipes.filter(tags__slug__in=tags).distinct()
        return recipes

    def filter_is_favorited(self, recipes, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return recipes

        return recipes.filter(
            favorites__user=user) if value else recipes.exclude(
                favorites__user=user)

    def filter_is_in_shopping_cart(self, recipes, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return recipes

        return recipes.filter(
            shopping_carts__user=user) if value else recipes.exclude(
                shopping_carts__user=user)
