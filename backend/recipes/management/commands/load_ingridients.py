"""
Команда для загрузки ингредиентов из JSON-файла.

Эта команда позволяет импортировать список ингредиентов с указанием их
названий и единиц измерения из JSON-файла в базу данных.
"""

from recipes.models import Ingredient
from .core import BaseLoadDataCommand


class Command(BaseLoadDataCommand):
    """Команда для загрузки ингредиентов из JSON-файла."""
    model = Ingredient
