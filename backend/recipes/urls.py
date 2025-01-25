from django.urls import path

from .views import recipe_redirect

urlpatterns = [
    path('s/<str:short_link>/', recipe_redirect, name='recipe-redirect'),

]
