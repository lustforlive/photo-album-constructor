# Makefile для управления проектом "Конструктор фотоальбомов"

.PHONY: up down restart build ps logs logs-web logs-celery migrate makemigrations seed superuser shell test clean help

# По умолчанию выводит справку по всем командам
help:
	@echo "Доступные команды для управления проектом:"
	@echo "  make up              - Запустить все контейнеры в фоновом режиме"
	@echo "  make down            - Остановить и удалить контейнеры"
	@echo "  make restart         - Перезапустить контейнеры"
	@echo "  make build           - Пересобрать Docker-образы"
	@echo "  make ps              - Показать статус контейнеров"
	@echo "  make logs            - Просмотр логов всех контейнеров в реальном времени"
	@echo "  make logs-web        - Просмотр логов контейнера Django (web)"
	@echo "  make logs-celery     - Просмотр логов контейнера Celery"
	@echo "  make migrate         - Выполнить миграции базы данных"
	@echo "  make makemigrations  - Создать новые миграции"
	@echo "  make seed            - Заполнить базу данных тестовыми данными"
	@echo "  make superuser       - Создать суперпользователя Django"
	@echo "  make shell           - Войти в интерактивную консоль Django"
	@echo "  make test            - Запустить тесты"
	@echo "  make clean           - Остановить контейнеры и очистить все Volumes (базу данных)"

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

build:
	docker compose build

ps:
	docker compose ps

logs:
	docker compose logs -f

logs-web:
	docker compose logs -f web

logs-celery:
	docker compose logs -f celery

migrate:
	docker compose exec web python manage.py migrate

makemigrations:
	docker compose exec web python manage.py makemigrations

seed:
	docker compose exec web python manage.py seed_db

superuser:
	docker compose exec web python manage.py createsuperuser

shell:
	docker compose exec web python manage.py shell

test:
	docker compose run --rm web python manage.py test

clean:
	docker compose down -v
