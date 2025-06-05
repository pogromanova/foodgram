from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
import re

def validate_username(value):
    if re.search(r'[^\w.@+-]', value):
        raise ValidationError('Имя пользователя содержит недопустимые символы')
    return value

class User(AbstractUser):
    """Модель пользователя."""
    
    email = models.EmailField(
        'Адрес электронной почты',
        max_length=254,
        unique=True,
    )
    username = models.CharField(
        'Имя пользователя', 
        max_length=150,
        unique=True,
        validators=[validate_username],
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
        blank=False, 
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        blank=False, 
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['id']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'