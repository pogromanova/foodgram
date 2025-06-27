from django.core.management.base import BaseCommand
from recipes.models import Ingredient
import csv
import os


class Command(BaseCommand):
    """Загружает ингредиенты из data/ingredients.csv (или альтернативных путей)."""

    help = 'Загрузка ингредиентов из CSV‑файла.'

    CSV_LOCATIONS = [
        '/app/data/ingredients.csv',
        './data/ingredients.csv',
        '../data/ingredients.csv',
        '../../data/ingredients.csv',
    ]

    def handle(self, *args, **options):
        csv_path = next(
            (p for p in self.CSV_LOCATIONS if os.path.exists(p)), None)

        if not csv_path:
            self.stdout.write(self.style.WARNING(
                'Файл ingredients.csv не найден – загрузка пропущена.'))
            return

        created, existed = 0, 0

        with open(csv_path, encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                name, unit = row[0].strip(), row[1].strip()
                if not (name and unit):
                    continue
                _, is_created = Ingredient.objects.get_or_create(
                    name=name, measurement_unit=unit)
                if is_created:
                    created += 1
                else:
                    existed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Ингредиенты загружены: создано {created}, уже существовало {existed}'
            )
        )
