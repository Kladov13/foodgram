import json

from django.core.management.base import BaseCommand


class BaseLoadDataCommand(BaseCommand):
    """Базовый класс для загрузки данных в базу."""
    model = None

    @property
    def file_to(self):
        return self.model._meta.verbose_name_plural.lower()

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help=f'Путь к JSON-файлу с {self.file_to}'
        )

    @property
    def help(self):
        return f'Загрузка {self.file_to} из JSON-файла'

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        try:
            with open(file_path, 'r') as file:
                created_objects = self.model.objects.bulk_create(
                    [self.model(**item) for item in json.load(
                        file).get(self.file_to, [])],
                    ignore_conflicts=True)
                self.stdout.write(self.style.SUCCESS(
                    f'{self.file_to} загружены. '
                    f'Добавлено {len(created_objects)}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(
                    f'Ошибка загрузки {self.file_to} из "{file_path}": {e}'
                    ))
