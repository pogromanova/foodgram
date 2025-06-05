from django.core.management.base import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    help = 'Загрузка тегов'

    def handle(self, *args, **options):
        tags_data = [
            {'name': 'Завтрак', 'slug': 'breakfast'},
            {'name': 'Обед', 'slug': 'lunch'},
            {'name': 'Ужин', 'slug': 'dinner'},
        ]
        
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(**tag_data)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Создан тег: {tag.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Тег уже существует: {tag.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Загрузка тегов завершена')
        )