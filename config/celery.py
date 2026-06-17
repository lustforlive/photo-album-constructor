import os
from celery import Celery

# Задаем переменную окружения для настроек Django по умолчанию
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Загружаем настройки из config/settings.py, используя префикс CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически ищем задачи (tasks.py) во всех установленных приложениях (в т.ч. 'albums')
app.autodiscover_tasks()