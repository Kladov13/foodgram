FIO_MAX_FIELD_LENGTH = 150
AVATAR_ERROR = 'Изображение отсутствует.'
SUBSCRIBE_SELF_ERROR = 'Нельзя подписаться на самого себя.'
RECIPES_LIMIT = 10000000
TAG_NAME_MAX_LENGTH = 32
INGREDIENT_NAME_MAX_LENGTH = 128
INGREDIENT_UNIT_MAX_LENGTH = 64
RECIPE_NAME_MAX_LENGTH = 256
COOKING_TIME_MIN = 1
COOKING_TIME_ERROR = (
    f'Время приготовления не может быть меньше {COOKING_TIME_MIN} минуты'
)
AMOUNT_MIN = 1
AMOUNT_OF_INGREDIENT_MIN_VALUE_ERROR = (
    f'Кол-во ингредиентов не меньше {AMOUNT_MIN}.'
)
AMOUNT_OF_INGREDIENT_CREATE_ERROR = (
    'Для создания рецепта необходим минимум 1 ингредиент'
)
AMOUNT_OF_TAG_CREATE_ERROR = (
    'Для создания рецепта необходим минимум 1 тэг.'
)
DUPLICATE_OF_INGREDIENT_CREATE_ERROR = (
    'Ингредиенты не должны повторяться в наборе рецепта.'
)
DUPLICATE_OF_TAG_CREATE_ERROR = (
    'Тэги не должны повторяться в наборе рецепта.'
)
DUPLICATE_OF_RECIPE_ADD_CART = (
    '{recipes} уже добавлен в выбранный список.'
)
UNEXIST_RECIPE_CREATE_ERROR = (
    '{recipes} не существует или удален.'
)
UNEXIST_SHOPPING_CART_ERROR = (
    'Данный список рецептов не существует или удален.'
)
SUBSCRIBE_ERROR = 'Вы уже подписаны на {author}.'
SUBSCRIBE_SELF_ERROR = 'Нельзя подписаться на самого себя.'
SUBSCRIBE_DELETE_ERROR = (
    'Невозможно удалить несуществующую подписку.'
)
EMAIL_MAX_LENGTH = 254
SHOPPING_LIST_HEADER = 'Список покупок для: {0} Дата: {1:%Y-%m-%d}\n'
INGREDIENT_FORMAT = '{0}. {1} ({2}) - {3}'
