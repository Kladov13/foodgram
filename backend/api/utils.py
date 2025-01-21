import base64
from datetime import datetime

from django.core.files.base import ContentFile
from django.http import FileResponse
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Кастомный класс для расширения стандартного ImageField."""

    def to_internal_value(self, data):
        """Метод для формата base64"""
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


def create_report_of_shopping_list(user, ingredients, recipes):
    """Функция для генерации отчета списка покупок для скачивания."""

    today = datetime.today()
    shopping_list_header = (
        'Список покупок для: {0}\n\n'
        'Дата: {1:%Y-%m-%d}\n\n'.format(user.get_full_name(), today)
    )
    shopping_list_ingredients = '\n'.join(
        '{0}. {1} ({2}) - {3}'.format(
            i, ingredient["ingredient__name"].capitalize(),
            ingredient["ingredient__measurement_unit"], ingredient["amount"])
        for i, ingredient in enumerate(ingredients, start=1)
    )
    shopping_list_recipes = '\n'.join(
        '{0}'.format(recipe.name) for recipe in recipes
    )
    shopping_list = '\n'.join([  # Перенос формирования отчета в вызывающий код
        shopping_list_header,
        'Продукты:',
        shopping_list_ingredients,
        'Рецепты:',
        shopping_list_recipes,
        '\n\nFoodgram'
    ])
    return shopping_list
