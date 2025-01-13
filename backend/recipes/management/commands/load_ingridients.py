"""
Команда для загрузки ингредиентов из JSON-файла.

Эта команда позволяет импортировать список ингредиентов с указанием их
названий и единиц измерения из JSON-файла в базу данных.
"""

import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для загрузки ингредиентов из JSON-файла."""

    help = 'Загрузка ингредиентов из JSON-файла'

    def add_arguments(self, parser):
        """
        Добавляет аргументы для команды.

        Аргументы:
            parser: объект для добавления пользовательских аргументов.
        """
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON-файлу с ингредиентами'
        )

    def handle(self, *args, **kwargs):
        """
        Обрабатывает выполнение команды.

        Читает JSON-файл, загружает данные и сохраняет их в базу данных.
        """
        file_path = kwargs['file_path']

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            ingredients = [
                Ingredient(
                    name=item['name'],
                    measurement_unit=item['measurement_unit']
                )
                for item in data
            ]
            Ingredient.objects.bulk_create(
                ingredients,
                ignore_conflicts=True
            )
            self.stdout.write(
                self.style.SUCCESS('Ингредиенты успешно загружены.')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Ошибка при загрузке ингредиентов: {e}')
            )
