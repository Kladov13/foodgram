from django.urls import path

from api.views import RecipeDetailView
from .views import recipe_redirect

urlpatterns = [
    path('recipes/<int:pk>/',
         RecipeDetailView.as_view(), name='recipe-detail'),
    path('s/<int:recipe_id>/', recipe_redirect, name='recipe-redirect'),
]
