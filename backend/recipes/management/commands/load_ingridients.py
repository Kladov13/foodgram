"""
Команда для загрузки ингредиентов из JSON-файла.

Эта команда позволяет импортировать список ингредиентов с указанием их
названий и единиц измерения из JSON-файла в базу данных.
"""

from recipes.models import Ingredient
from .core import BaseLoadDataCommand


class Command(BaseLoadDataCommand):
    """Команда для загрузки ингредиентов из JSON-файла."""

    help = 'Загрузка ингредиентов из JSON-файла'

    def __init__(self):
        super().__init__(Ingredient, 'ingredients')
