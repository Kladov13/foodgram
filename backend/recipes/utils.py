from datetime import datetime
from uuid import uuid4

from django.http import HttpResponse

from api.constants import MAX_LENGTH_SHORT_LINK


def generate_short_link():
    """Функция для генерации короткой ссылки."""
    return uuid4().hex[:MAX_LENGTH_SHORT_LINK]


def create_report_of_shopping_list(user, ingredients):
    """Функция для генерации отчета списка покупок для скачивания."""
    today = datetime.today()
    shopping_list = (
        f'Список покупок для: {user.get_full_name()}\n\n'
        f'Дата: {today:%Y-%m-%d}\n\n'
    )
    shopping_list += '\n'.join([
        f'- {ingredient["ingredient__name"]} '
        f'({ingredient["ingredient__measurement_unit"]})'
        f' - {ingredient["amount"]}'
        for ingredient in ingredients
    ])
    shopping_list += f'\n\nFoodgram ({today:%Y})'

    filename = f'{user.username}_shopping_list.txt'
    response = HttpResponse(shopping_list, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response
