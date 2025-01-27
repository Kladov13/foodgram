import json

from django.core.management.base import BaseCommand


class BaseLoadDataCommand(BaseCommand):
    """Базовый класс для загрузки данных в базу."""

    def __init__(self, model, fileto):
        self.model = model
        self.fileto = fileto
        super().__init__()

    def add_arguments(self, parser):
        """Добавляет аргументы для команды."""
        parser.add_argument(
            'file_path',
            type=str,
            help=f'Путь к JSON-файлу с {self.fileto}'  # Путь к файлу
        )

    def handle(self, *args, **kwargs):
        """Обрабатывает выполнение команды."""
        file_path = kwargs['file_path']
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                # Если JSON-файл является списком (не словарем)
                if isinstance(data, list):
                    items = [self.model(**item) for item in data]
                else:
                    # Если это словарь, ищем нужное поле
                    items = [self.model(**item) for item in data.get(
                        self.fileto, [])]
                # Загружаем данные в базу
                count = self.model.objects.bulk_create(
                    items, ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(
                f'{self.fileto.capitalize()} загружены. Добавлено {len(count)}'
            ))
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(
                    f'Ошибка при загрузке {self.fileto} из "{file_path}": {e}')
            )
