from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from recipes.models import Tag, Ingredient
import csv
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Загрузка начальных данных: тегов и ингредиентов'

    def handle(self, *args, **options):
        tags_data = [
            {'name': 'Завтрак', 'slug': 'breakfast'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Ужин', 'slug': 'dinner'},
        ]
        
        self.stdout.write('Создание тегов...')
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(**tag_data)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Создан тег: {tag.name}')
                )
            else:
                self.stdout.write(f'Тег {tag.name} уже существует')

        
        csv_path = '/app/data/ingredients.csv'
        
        self.stdout.write(f'Поиск файла ингредиентов: {csv_path}')
        
        if not os.path.exists(csv_path):
            alternative_paths = [
                './data/ingredients.csv',
                '../data/ingredients.csv',
                '../../data/ingredients.csv'
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    csv_path = alt_path
                    self.stdout.write(f'Найден файл по пути: {csv_path}')
                    break
            else:
                self.stdout.write(
                    self.style.ERROR(f'Файл ingredients.csv не найден!')
                )
                return
        
        self.stdout.write('Загрузка ингредиентов...')
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            ingredients_created = 0
            ingredients_existed = 0
            
            for row in reader:
                if len(row) >= 2:
                    name = row[0].strip()
                    measurement_unit = row[1].strip()
                    
                    if name and measurement_unit:
                        ingredient, created = Ingredient.objects.get_or_create(
                            name=name,
                            measurement_unit=measurement_unit
                        )
                        
                        if created:
                            ingredients_created += 1
                        else:
                            ingredients_existed += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка завершена! '
                f'Создано ингредиентов: {ingredients_created}, '
                f'уже существовало: {ingredients_existed}'
            )
        )
        
        self.stdout.write('Для создания суперпользователя выполните: python manage.py createsuperuser')