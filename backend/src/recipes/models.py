from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import UniqueConstraint, CheckConstraint, Q, F
from users.models import User


class Ingredient(models.Model):
    name = models.CharField('Наименование', max_length=128)
    measurement_unit = models.CharField('Единица измерения', max_length=64)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measurement_unit',
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    name = models.CharField('Название блюда', max_length=256, db_index=True)
    text = models.TextField('Описание процесса приготовления')
    author = models.ForeignKey(
        User,
        related_name='authored_recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
    )
    image = models.ImageField(
        'Изображение готового блюда', upload_to='recipe_photos/')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeComponent',
        related_name='used_in_recipes',
        verbose_name='Список ингредиентов',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (мин)',
        validators=[MinValueValidator(
            1, message='Время должно быть не менее 1 минуты')],
    )
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']
        default_related_name = 'recipe_entries'

    def __str__(self):
        return f'"{self.name}" от {self.author.username}'


class RecipeComponent(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        related_name='components',
        on_delete=models.CASCADE,
        verbose_name='В рецепте',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='recipe_usage',
        on_delete=models.CASCADE,
        verbose_name='Продукт',
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(
            1, message='Требуется хотя бы 1 единица')],
    )

    class Meta:
        verbose_name = 'Компонент рецепта'
        verbose_name_plural = 'Компоненты рецептов'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_for_recipe',
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} ({self.amount} '
            f'{self.ingredient.measurement_unit}) для "{self.recipe.name}"'
        )


class UserFavorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name='favorite_recipes',
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_favorites',
        on_delete=models.CASCADE,
        verbose_name='Избранный рецепт',
    )
    added_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ['-added_at']
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_user_favorite'),
            CheckConstraint(check=~Q(user=None), name='user_not_null'),
        ]

    def __str__(self):
        return f'{self.user.username} добавил "{self.recipe.name}" в избранное'


class GroceryList(models.Model):
    user = models.ForeignKey(
        User,
        related_name='grocery_list',
        on_delete=models.CASCADE,
        verbose_name='Владелец списка',
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_grocery_lists',
        on_delete=models.CASCADE,
        verbose_name='Рецепт в списке',
    )
    added_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ['-added_at']
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_recipe_in_list')
        ]

    def __str__(self):
        return f'{self.user.username}: "{self.recipe.name}" в списке покупок'
