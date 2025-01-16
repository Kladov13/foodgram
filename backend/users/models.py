from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import FIO_MAX_FIELD_LENGTH


class User(AbstractUser):
    """Кастомный класс для модели User."""

    email = models.EmailField('Email', unique=True, error_messages={
        'unique': 'Данный адрес электронной почты уже используется.',
    })
    first_name = models.CharField('Имя', max_length=FIO_MAX_FIELD_LENGTH)
    last_name = models.CharField('Фамилия', max_length=FIO_MAX_FIELD_LENGTH)

    # Поле для аватара.
    avatar = models.ImageField(
        upload_to='users/images/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    subscribers = models.ManyToManyField(
        'self', related_name='subscribed_users', through='Subscription'
    )

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписок."""

    followed = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followings',
        verbose_name='Автор рецепта'
    )
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followers',
        verbose_name='Подписчик'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'list_subscription'
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.followed.__str__()} -> {self.follower.__str__()}'
