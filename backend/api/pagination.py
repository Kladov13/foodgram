from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """Кастомный класс для пагинации."""

    page_size_query_param = 'limit'
    page_query_param = 'page'
    max_page_size = 6
