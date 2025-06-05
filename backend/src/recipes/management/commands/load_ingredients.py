import csv
import os
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Загрузка ингредиентов из CSV файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Путь к CSV файлу с ингредиентами',
        )

    def handle(self, *args, **options):
        if options['path']:
            csv_path = options['path']
        else:
            csv_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
                'data', 'ingredients.csv'
            )
        
        self.stdout.write(f'Загрузка ингредиентов из: {csv_path}')
        
        if not os.path.exists(csv_path):
            self.stdout.write(
                self.style.ERROR(f'Файл {csv_path} не найден!')
            )
            return
        
        ingredients_created = 0
        ingredients_existed = 0
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            
            for row_num, row in enumerate(reader, 1):
                if len(row) < 2:
                    self.stdout.write(
                        self.style.WARNING(f'Строка {row_num}: недостаточно данных - {row}')
                    )
                    continue
                
                name = row[0].strip()
                measurement_unit = row[1].strip()
                
                if not name or not measurement_unit:
                    self.stdout.write(
                        self.style.WARNING(f'Строка {row_num}: пустые поля - {row}')
                    )
                    continue
                
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name,
                    defaults={'measurement_unit': measurement_unit}
                )
                
                if created:
                    ingredients_created += 1
                else:
                    ingredients_existed += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка завершена!\n'
                f'Создано новых ингредиентов: {ingredients_created}\n'
                f'Уже существовало: {ingredients_existed}\n'
                f'Всего ингредиентов в базе: {Ingredient.objects.count()}'
            )
        )