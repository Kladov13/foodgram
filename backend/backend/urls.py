from django.contrib import admin
from django.urls import path, include

from api.views import RecipeRedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls', namespace='api')),
    path(
        's/<str:short_link>/', RecipeRedirectView.as_view(),
        name='recipe-redirect'
    ),
]
