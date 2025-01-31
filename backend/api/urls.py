from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter


from .views import (
    IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet
)


app_name = 'api'

api = DefaultRouter()

api.register('ingredients', IngredientViewSet, basename='ingredient')
api.register('recipes', RecipeViewSet, basename='recipe')
api.register('tags', TagViewSet, basename='tag')
api.register('users', UserViewSet, basename='users')


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(api.urls))
]
