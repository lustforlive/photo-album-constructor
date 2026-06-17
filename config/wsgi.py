"""
WSGI config for the project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os

from django.core.wsgi import get_wsgi_application

# Указываем путь к нашим настройкам
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаем WSGI приложение
application = get_wsgi_application()