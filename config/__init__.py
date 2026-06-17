# Этот импорт гарантирует, что приложение Celery загружается
# при старте Django, чтобы декоратор @shared_task мог его использовать.

from .celery import app as celery_app

__all__ = ('celery_app',)