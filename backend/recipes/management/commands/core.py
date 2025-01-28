import json

from django.core.management.base import BaseCommand


class BaseLoadDataCommand(BaseCommand):
    """Базовый класс для загрузки данных в базу."""
    model = None

    @property
    def file_to(self):
        return self.model.__name__.lower() + 's'

    def add_arguments(self, parser):
        """Добавляет аргументы для команды."""
        parser.add_argument(
            'file_path',
            type=str,
            help=f'Путь к JSON-файлу с {self.file_to}'
        )

    @property
    def help(self):
        return f'Загрузка {self.file_to} из JSON-файла'

    def handle(self, *args, **kwargs):
        """Обрабатывает выполнение команды."""
        file_path = kwargs['file_path']
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                items_data = data if isinstance(data, list) else data.get(
                    self.file_to, [])
                items = [self.model(**item) for item in items_data]
                created_objects = self.model.objects.bulk_create(
                    items, ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(
                    f'{self.file_to.capitalize()} загружены. '
                    f'Добавлено {len(created_objects)}'
                ))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f'Ошибка при загрузке {self.file_to} из "{file_path}": {e}')
            )
