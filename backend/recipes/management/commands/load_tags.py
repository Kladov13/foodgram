import json
import os

from django.core.management.base import BaseCommand
from recipes.models import Tag
from django.conf import settings


class Command(BaseCommand):
    """Команда для загрузки ингредиентов из JSON-файла."""

    help = 'Загрузка тегов из JSON-файла'

    def add_arguments(self, parser):
        """
        Добавляет аргументы для команды.

        Аргументы:
            parser: объект для добавления пользовательских аргументов.
        """
        parser.add_argument(
            'file_path',
            type=str,
            help='Путь к JSON-файлу с тегами'
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

            tags = [
                Tag(
                    name=item['name'],
                    slug=item['slug']
                )
                for item in data['tags']
            ]
            Tag.objects.bulk_create(
                tags,
                ignore_conflicts=True
            )
            self.stdout.write(
                self.style.SUCCESS('Tеги успешно загружены.')
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'Ошибка при загрузке тегов: {e}')
            )
