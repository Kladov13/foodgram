from django.urls import path

from .views import recipe_redirect

urlpatterns = [
    path('recipes/<int:pk>/',
         recipe_redirect, name='recipe-detail'),
    path('s/<int:pk>/', recipe_redirect, name='recipe-redirect'),
]
