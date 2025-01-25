from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse, FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser import views as DjoserViewSets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
)

from recipes.constants import (
    UNEXIST_RECIPE_CREATE_ERROR, DUPLICATE_OF_RECIPE_ADD_CART,
    UNEXIST_SHOPPING_CART_ERROR,
    CHANGE_AVATAR_ERROR_MESSAGE, SUBSCRIBE_ERROR_MESSAGE,
    SUBSCRIBE_SELF_ERROR_MESSAGE

)
from .filters import RecipeFilter, IngredientFilter
from recipes.models import (
    Ingredient, Favorite, Recipe, RecipeIngredients,
    ShoppingCart, Tag, Subscription, User

)
from .serializers import (
    IngredientSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    TagSerializer,
    SubscriberReadSerializer,
    AvatarSerializer,
    BaseUserSerializer
)
from .permissions import (
    IsAuthor
)
from .utils import create_report_of_shopping_list
from .pagination import PageLimitPagination


class UserViewSet(DjoserViewSets.UserViewSet):
    """Общий вьюсет для пользователя."""

    queryset = User.objects.all()
    serializer_class = BaseUserSerializer
    pagination_class = PageLimitPagination

    @action(
        ["get", "put", "patch", "delete"],
        detail=False,
    )
    def get_permissions(self):
        """
        Метод для управления правами доступа.
        Переопределяется для изменения прав доступа в методе `me`.
        """
        if self.action == 'me':
            # Разрешаем доступ всем аутентифицированным пользователям
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        ['PUT', 'DELETE'],
        detail=False,
        url_path='me/avatar'
    )
    def change_avatar(self, request, *args, **kwargs):
        """Метод для управления аватаром."""
        user = self.request.user
        if request.method == 'DELETE':
            if user.avatar:
                # Удаление файла с диска
                user.avatar.delete(save=True)
                # Удаление ссылки на аватар в базе данных
                self.request.user.avatar = None
                self.request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if 'avatar' not in request.data:
            raise ValidationError({'error': CHANGE_AVATAR_ERROR_MESSAGE})

        serializer = AvatarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        avatar_data = serializer.validated_data.get('avatar')
        user.avatar = avatar_data
        user.save()
        image_url = request.build_absolute_uri(
            f'/media/users/{avatar_data.name}')
        return Response(
            {'avatar': str(image_url)}, status=status.HTTP_200_OK
        )

    @action(['GET'], detail=False, url_path='subscriptions')
    def subscriptions(self, request):
        """Метод для управления подписками пользователя."""
        user = request.user
        queryset = User.objects.filter(followers__subscriber=user)
        pages = self.paginate_queryset(queryset)
        self.serializer_class = SubscriberReadSerializer
        serializer = self.get_serializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=('POST', 'DELETE'),
            url_path='subscribe', url_name='subscribe')
    def subscribe(self, request, id):
        """Метод для управления подписками."""
        user = request.user
        author = get_object_or_404(User, id=id)

        # Проверка подписки на самого себя
        if user == author:
            raise ValidationError({'error': SUBSCRIBE_SELF_ERROR_MESSAGE})

        # Логика добавления подписки
        if request.method == 'POST':
            subscription_exists = Subscription.objects.filter(
                author=author, subscriber=user)
            if subscription_exists.exists():
                raise ValidationError(
                    {'error': 'Вы уже подписаны на этого автора.'})
            # Создание новой подписки
            Subscription.objects.create(author=author, subscriber=user)
            serializer = SubscriberReadSerializer(
                author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Логика удаления подписки
        subscription_exists = get_object_or_404(
            Subscription, author=author, subscriber=user)
        subscription_exists.delete()
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)



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
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, ]
    filterset_class = RecipeFilter
    serializer_class = RecipeSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.prefetch_related('favorites', 'shoppingcarts')
        return queryset

    def get_permissions(self):
        """Метод для прав доступа, в зависимости от метода."""
        if self.request.method in ("PATCH", "DELETE"):
            self.permission_classes = [IsAuthor]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Метод для создания рецепта."""
        serializer.save(author=self.request.user)

    @action(detail=True,
            methods=['GET'], url_path='get-link', url_name='get-link')
    def get_short_link(self, request, pk):
        if not Recipe.objects.filter(id=pk).exists():
            raise ValidationError(
                {'status':
                 f'Рецепт с ID {pk} не найден'})
        short_link = f'{request.build_absolute_uri("/")[:-1]}/{str(pk)}/'
        return JsonResponse({'short-link': short_link})

    @action(detail=True, methods=['POST', 'DELETE'])
    def shopping_cart(self, request, pk):
        """Общий метод для добавления/удаления рецептов в список покупок."""
        if request.method == 'POST':
            return self.common_add_to(ShoppingCart, request.user, pk)
        return self.common_delete_from(ShoppingCart, request.user, pk)

    @action(detail=True, methods=['POST', 'DELETE'])
    def favorite(self, request, pk):
        """Общий метод для добавления/удаления рецептов в избранное."""
        if request.method == 'POST':
            return self.common_add_to(Favorite, request.user, pk)
        return self.common_delete_from(Favorite, request.user, pk)

    def common_add_to(self, model, user, pk):
        """Общий метод для добавления рецепта в список покупок или избранное"""
        recipe = get_object_or_404(Recipe, id=pk)
        obj, created = model.objects.get_or_create(
            user=user, recipe=get_object_or_404(Recipe, id=pk))
        if not created:
            raise ValidationError({'error': DUPLICATE_OF_RECIPE_ADD_CART})
        serializer = RecipeShortSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def common_delete_from(self, model, user, pk):
        """ 
        Общий метод для удаления рецепта из списка покупок или избранного. 
        """
        obj = model.objects.filter(user=user, recipe_id=pk)
        
        # Удаляем объект, если он существует
        get_object_or_404(obj).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        """Метод для скачивания списка покупок."""
        user = request.user
        if not user.shoppingcarts.exists():
            raise ValidationError({'error': UNEXIST_SHOPPING_CART_ERROR})
        ingredients = RecipeIngredients.objects.filter(
            recipe__shoppingcarts__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')
        recipes = Recipe.objects.filter(shoppingcarts__user=user)
        shopping_list = create_report_of_shopping_list(
            user, ingredients, recipes)
        # Формирование имени файла
        filename = f'{user.username}_shopping_list.txt'
        # Возвращаем файл для скачивания
        return FileResponse(
            shopping_list,
            as_attachment=True,
            filename=filename,
            content_type='text/plain'
        )
