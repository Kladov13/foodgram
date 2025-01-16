from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    IngredientViewSet, RecipeViewSet, TagViewSet,
)
from users.views import UserViewSet

app_name = 'api'

api_v1 = DefaultRouter()

api_v1.register('ingredients', IngredientViewSet, basename='ingredient')
api_v1.register('recipes', RecipeViewSet, basename='recipe')
api_v1.register('tags', TagViewSet, basename='tag')
api_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(api_v1.urls)),
]
