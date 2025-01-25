import base64
from datetime import datetime

from django.core.files.base import ContentFile
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


SHOPPING_LIST_HEADER = 'Список покупок для: {0}\n\nДата: {1:%Y-%m-%d}\n\n'
INGREDIENT_FORMAT = '{0}. {1} ({2}) - {3}'

def create_report_of_shopping_list(user, ingredients, recipes):
    """Функция для генерации отчета списка покупок для скачивания."""

    today = datetime.today()
    # Формирование заголовка
    shopping_list_header = SHOPPING_LIST_HEADER.format(user.get_full_name(), today)
    # Формирование списка ингредиентов
    shopping_list_ingredients = '\n'.join(
        INGREDIENT_FORMAT.format(
            i, ingredient['ingredient__name'].capitalize(),
            ingredient['ingredient__measurement_unit'], ingredient['amount'])
        for i, ingredient in enumerate(ingredients, start=1)
    )
    # Формирование списка рецептов
    shopping_list_recipes = '\n'.join(recipe.name for recipe in recipes)
    # Возвращаем сформированный список покупок
    return '\n'.join([
        shopping_list_header,
        'Продукты:',
        shopping_list_ingredients,
        'Рецепты:',
        shopping_list_recipes,
        '\n\nFoodgram'
    ])
