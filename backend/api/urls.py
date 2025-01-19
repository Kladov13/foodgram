from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet
)
from recipes.controllers import recipe_redirect


app_name = 'api'

api = DefaultRouter()

api.register('ingredients', IngredientViewSet, basename='ingredient')
api.register('recipes', RecipeViewSet, basename='recipe')
api.register('tags', TagViewSet, basename='tag')
api.register('users', UserViewSet, basename='users')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(api.urls)),
    path('<str:short_link>/', recipe_redirect, name='recipe-redirect'),
]
