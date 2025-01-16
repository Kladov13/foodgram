from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, redirect
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import (
    UNEXIST_RECIPE_CREATE_ERROR, DUPLICATE_OF_RECIPE_ADD_CART,
    UNEXIST_SHOPPING_CART_ERROR

)
from .filters import RecipeFilter, IngredientFilter
from recipes.models import (
    Ingredient, Favorite, Recipe, RecipeIngredients,
    ShoppingCart, Tag
)
from .serializers import (
    IngredientSerializer,
    RecipeCreateSerializer,
    ShortRecipeSerializer,
    TagSerializer,
)
from users.permissions import (
    IsAuthor,
    ReadOnly
)
from recipes.utils import create_report_of_shopping_list


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для Тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для Ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [IngredientFilter, ]
    permission_classes = [AllowAny]
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для Рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = [ReadOnly]
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter
    serializer_class = RecipeCreateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.prefetch_related('favorites', 'shopping_cart')
        return queryset

    def get_permissions(self):
        """Метод для прав доступа, в зависимости от метода."""
        if self.request.method in ("GET", "POST"):
            self.permission_classes = [IsAuthenticated | ReadOnly]
        elif self.request.method in ("PATCH", "DELETE"):
            self.permission_classes = [IsAuthor]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Метод для создания рецепта."""
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['GET'], url_path='get-link')
    def get_short_link(self, request, pk):
        try:
            recipe = self.get_object()
        except Recipe.DoesNotExist:
            return Response(
                {'message': UNEXIST_RECIPE_CREATE_ERROR},
                status=status.HTTP_404_NOT_FOUND
            )

        scheme = request.scheme
        host = request.get_host()
        domain = f'{scheme}://{host}'
        return Response(
            {'short-link': f'{domain}/s/{recipe.short_link}'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk):
        """Общий метод для добавления/удаления рецептов в список покупок."""
        if request.method == 'POST':
            return self.common_add_to(ShoppingCart, request.user, pk)
        else:
            return self.common_delete_from(ShoppingCart, request.user, pk)

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk):
        """Общий метод для добавления/удаления рецептов в избранное."""
        if request.method == 'POST':
            return self.common_add_to(Favorite, request.user, pk)
        else:
            return self.common_delete_from(Favorite, request.user, pk)

    def common_add_to(self, model, user, pk):
        """Общий метод для добавления рецепта в список покупок или избранное"""
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response(
                {'errors': DUPLICATE_OF_RECIPE_ADD_CART},
                status=status.HTTP_400_BAD_REQUEST
            )
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = ShortRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def common_delete_from(self, model, user, pk):
        """
        Общий метод для удаления рецепта из списка покупок или избранного.
        """
        recipe = get_object_or_404(Recipe, id=pk)

        obj = model.objects.filter(user=user, recipe=recipe)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'errors': UNEXIST_RECIPE_CREATE_ERROR},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        """Метод для скачивания списка покупок."""
        user = request.user
        if not user.shopping_cart.exists():
            return Response(
                {'errors': UNEXIST_SHOPPING_CART_ERROR},
                status=status.HTTP_400_BAD_REQUEST)
        ingredients = RecipeIngredients.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))
        return create_report_of_shopping_list(user, ingredients)


class RecipeRedirectView(APIView):
    permission_classes = [ReadOnly]

    def get(self, request, short_link):
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return redirect(recipe.get_absolute_url())
