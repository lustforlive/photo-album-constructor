from django.core.management.base import BaseCommand
from albums.models import Role, AlbumFormat, User, Project, Order, OrderItem

class Command(BaseCommand):
    help = 'Заполняет базу данных демонстрационными данными'

    def handle(self, *args, **kwargs):
        # Очищаем старые данные (чтобы при повторном запуске скрипта не было дублей)
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Project.objects.all().delete()
        AlbumFormat.objects.all().delete()
        User.objects.all().delete()
        Role.objects.all().delete()

        # 1. Роли
        role_admin = Role.objects.create(name='Администратор')
        role_client = Role.objects.create(name='Клиент')

        # 2. Пользователи (в рамках нашей модели User, а не стандартной Django)
        admin_user = User.objects.create(
            role=role_admin,
            email='admin@example.com',
            password_hash='dummy_hash_1'
        )
        client_user = User.objects.create(
            role=role_client,
            email='client@example.com',
            password_hash='dummy_hash_2'
        )

        # 3. Форматы альбомов
        format_premium = AlbumFormat.objects.create(
            name='Премиум 20х20 (Твердая обложка)',
            base_price=2500.00,
            created_by_user=admin_user
        )
        format_standard = AlbumFormat.objects.create(
            name='Стандарт 15х15 (Мягкая обложка)',
            base_price=1200.00,
            created_by_user=admin_user
        )

        # Добавляем клиенту избранные форматы (демонстрация M2M связи)
        client_user.favorite_formats.add(format_premium, format_standard)

        # 4. Проекты альбомов
        project_draft = Project.objects.create(
            user=client_user,
            format=format_premium,
            title='Свадебный альбом (в процессе)',
            status='Draft'
        )
        project_ready = Project.objects.create(
            user=client_user,
            format=format_standard,
            title='Отпуск на море 2023',
            status='Ready'
        )

        # 5. Заказ
        order = Order.objects.create(
            user=client_user,
            total_amount=3700.00,
            status='Created'
        )

        # 6. Позиции заказа (оба проекта в одном заказе)
        OrderItem.objects.create(
            order=order, project=project_draft, 
            quantity=1, price_at_moment=2500.00
        )
        OrderItem.objects.create(
            order=order, project=project_ready, 
            quantity=1, price_at_moment=1200.00
        )

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена тестовыми данными!'))
