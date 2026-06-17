from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from albums.models import PhotoAlbum

class Command(BaseCommand):
    help = 'Удаление пустых черновиков фотоальбомов, которые не обновлялись больше 30 дней'

    def handle(self, *args, **kwargs):
        # Вычисляем дату "30 дней назад" от текущего момента
        cutoff_date = timezone.now() - timedelta(days=30)
        
        # Находим альбомы: статус "Draft", 0 страниц, старее cutoff_date
        albums_to_delete = PhotoAlbum.objects.annotate(
            pages_count=Count('pages')
        ).filter(
            status='Draft',
            pages_count=0,
            updated_at__lt=cutoff_date
        )
        
        # Удаляем найденные записи
        deleted_count, _ = albums_to_delete.delete()
        
        self.stdout.write(self.style.SUCCESS(f'Успешно удалено пустых альбомов-черновиков: {deleted_count}'))