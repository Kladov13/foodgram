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
        f'Список покупок для: {user.get_full_name()}\n\n'
        f'Дата: {today:%Y-%m-%d}\n\n'
    )

    shopping_list_ingredients = '\n'.join([
        f'{i+1}. {ingredient["ingredient__name"].capitalize()} '
        f'({ingredient["ingredient__measurement_unit"]}) - {ingredient["amount"]}'
        for i, ingredient in enumerate(ingredients)
    ])

    shopping_list_recipes = '\n'.join([
        f'{recipe.name}'
        for recipe in recipes
    ])

    shopping_list = '\n'.join([
        shopping_list_header,
        'Продукты:',
        shopping_list_ingredients,
        'Рецепты:',
        shopping_list_recipes,
        f'\n\nFoodgram ({today:%Y})'
    ])

    filename = f'{user.username}_shopping_list.txt'

    # Включение FileResponse, чтобы корректно отправить файл
    response = FileResponse(
        shopping_list.encode('utf-8'),
        as_attachment=True,
        filename=filename,
        content_type='text/plain'
    )

    return response
