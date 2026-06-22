from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from .models import PhotoAlbum, Photo
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_printing_email(self, album_id):
    """
    Отправка email при отправке альбома на печать
    Выполняется асинхронно в фоновом воркере Celery
    """
    try:
        album = PhotoAlbum.objects.get(id=album_id)

        # Рендеринг HTML-письма
        context = {
            'album_title': album.title,
            'pages_count': album.pages.count(),
            'user_name': album.user.first_name or album.user.username,
            'order_date': album.updated_at.strftime('%d.%m.%Y'),
            'estimated_delivery': 'через 5-7 рабочих дней'
        }

        html_message = f"""
        <h2>Ваш альбом отправлен на печать!</h2>
        <p>Здравствуйте, {context['user_name']}!</p>
        <p>Ваш альбом "<strong>{context['album_title']}</strong>" 
           ({context['pages_count']} страниц) успешно отправлен на печать.</p>
        <p><strong>Дата заказа:</strong> {context['order_date']}</p>
        <p><strong>Примерная доставка:</strong> {context['estimated_delivery']}</p>
        <p>Спасибо за ваш заказ!</p>
        """

        send_mail(
            subject=f"Альбом '{album.title}' отправлен на печать",
            message="Смотрите письмо в HTML формате",
            from_email='orders@photoalbum.local',
            recipient_list=[album.user.email],
            html_message=html_message,
            fail_silently=False
        )

        logger.info(f"Email отправлен пользователю {album.user.email} для альбома {album_id}")

    except PhotoAlbum.DoesNotExist:
        logger.error(f"Альбом {album_id} не найден")
    except Exception as exc:
        logger.error(f"Ошибка при отправке email: {exc}")
        # Повтор задачи через 60 секунд
        self.retry(exc=exc, countdown=60)


@shared_task
def generate_daily_statistics():
    """
    Генерация ежедневной статистики
    Выполняется по расписанию (через Celery Beat)
    """
    from django.utils import timezone
    from datetime import timedelta

    yesterday = timezone.now() - timedelta(days=1)

    albums_created = PhotoAlbum.objects.filter(
        created_at__gte=yesterday,
        created_at__lt=timezone.now()
    ).count()

    photos_uploaded = Photo.objects.filter(
        created_at__gte=yesterday,
        created_at__lt=timezone.now()
    ).count()

    logger.info(f"Статистика за вчера: {albums_created} альбомов, {photos_uploaded} фото")

    return {
        'albums_created': albums_created,
        'photos_uploaded': photos_uploaded,
    }


@shared_task
def process_image_thumbnail(photo_id):
    """
    Создание миниатюр изображения
    Выполняется асинхронно для тяжелых операций
    """
    try:
        from PIL import Image
        import os

        photo = Photo.objects.get(id=photo_id)

        # Создать миниатюру
        if photo.file:
            img = Image.open(photo.file.path)
            img.thumbnail((200, 200))

            # Сохранить миниатюру
            thumb_path = f"{photo.file.path}_thumb.jpg"
            img.save(thumb_path, 'JPEG')

            logger.info(f"Миниатюра создана для фото {photo_id}")

    except Photo.DoesNotExist:
        logger.error(f"Фото {photo_id} не найдено")
    except Exception as exc:
        logger.error(f"Ошибка при создании миниатюры: {exc}")