from recipes.models import Tag
from .core import BaseLoadDataCommand


class Command(BaseLoadDataCommand):
    """Команда для загрузки тегов из JSON-файла."""

    help = 'Загрузка тегов из JSON-файла'

    def __init__(self):
        super().__init__(Tag, 'tags')
