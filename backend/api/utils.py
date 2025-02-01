import base64
from datetime import datetime

from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.constants import (
    INGREDIENT_FORMAT, SHOPPING_LIST_HEADER, MONTH_NAMES
)


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
    date = f"{today.day} {MONTH_NAMES[today.month - 1]} {today.year}"
    # Формирование заголовка
    shopping_list_header = SHOPPING_LIST_HEADER.format(
        user.username, date)
    # Формирование списка ингредиентов
    shopping_list_ingredients = '\n'.join(
        INGREDIENT_FORMAT.format(
            i, ingredient['ingredient__name'].capitalize(),
            ingredient['ingredient__measurement_unit'], ingredient['amount'])
        for i, ingredient in enumerate(ingredients, start=1)
    )
    # Формирование списка рецептов
    shopping_list_recipes = '\n'.join(
        f"{recipe.name} (автор: {recipe.author.username})"
        for recipe in recipes
    )
    # Возвращаем сформированный список покупок
    return '\n'.join([
        shopping_list_header,
        'Продукты:',
        shopping_list_ingredients,
        'Рецепты:',
        shopping_list_recipes,
        '\n\nFoodgram'
    ])
