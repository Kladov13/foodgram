from django.urls import path, include
from .views import recipe_redirect

urlpatterns = [
    path('<str:short_link>/', recipe_redirect, name='recipe-redirect'),
    path('s/', include('api.urls')),
]
