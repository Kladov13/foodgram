from recipes.models import Tag
from .core import BaseLoadDataCommand


class Command(BaseLoadDataCommand):
    """Команда для загрузки тегов из JSON-файла."""
    model = Tag
