import random
from io import BytesIO
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from albums.models import (Role, AlbumFormat, UserProfile, UserImage,
                           Project, Order, OrderItem, CoverType, Photo, 
                           PhotoAlbum, AlbumPage, PhotoPlacement)

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми записями (минимум по 10 для каждой таблицы)'

    def generate_dummy_image(self, name="dummy.jpg"):
        """Генерирует квадратик случайного цвета, чтобы ImageField работал корректно"""
        file_obj = BytesIO()
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        image = Image.new("RGB", (400, 400), color=color)
        image.save(file_obj, format="JPEG")
        file_obj.seek(0)
        return SimpleUploadedFile(name, file_obj.read(), content_type="image/jpeg")

    def handle(self, *args, **kwargs):
        self.stdout.write("Начинаем генерацию данных...")

        # 1. Роли (10 штук)
        role_names = ["Администратор", "Модератор", "Пользователь", "Гость", 
                      "VIP-клиент", "Дизайнер", "Менеджер", "Тестировщик", "Аналитик", "Разработчик"]
        roles = [Role.objects.get_or_create(name=name)[0] for name in role_names]

        # 2. Пользователи и Профили (10 штук)
        users = []
        usernames = ["dariagoryachko", "user1", "user2", "client2026", "tester", 
                     "moderator_main", "dev_go", "react_ninja", "polytech_student", "guest_99"]
        
        for i, username in enumerate(usernames):
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': f"{username}@example.com",
                'first_name': f"Имя_{i}",
                'last_name': f"Фамилия_{i}"
            })
            if created:
                user.set_password("password123")
                user.save()
            users.append(user)

            UserProfile.objects.get_or_create(user=user, defaults={
                'role': random.choice(roles)
            })

        # 3. Фотографии пользователей (UserImage - 10 штук)
        for i in range(10):
            UserImage.objects.get_or_create(
                user=random.choice(users),
                image_url=f"https://s3.example.com/avatars/user_{i}.jpg",
                file_size_kb=random.randint(100, 5000)
            )

        # 4. Форматы альбомов (10 штук)
        format_names = ["10x10 см", "15x15 см", "20x20 см", "20x30 см", "30x30 см", 
                        "А4 Вертикальный", "А4 Горизонтальный", "А5 Мини", "Квадратный Макс", "Панорамный"]
        formats = []
        for name in format_names:
            fmt, _ = AlbumFormat.objects.get_or_create(
                name=name, 
                defaults={'base_price': random.randint(500, 5000), 'created_by_user': users[0]}
            )
            formats.append(fmt)

        # 5. Типы обложек (10 штук)
        cover_names = ["Стандартный картон", "Матовая кожа", "Глянцевый пластик", "Тканевая обложка", 
                       "Премиум кожа", "Деревянная обложка", "Софт-тач", "Фотокнижная обложка", 
                       "Пружинный переплет", "Сшитая вручную"]
        covers = [CoverType.objects.get_or_create(name=name)[0] for name in cover_names]

        # 6. Загруженные фото (Photo - 10 штук)
        photos = []
        photo_titles = ["Пикачу", "Сборка на Go", "Универ", "Код React", "UML Диаграмма классов", 
                        "Архитектура проекта", "Группа 241-321", "Новый билд", "Логи терминала", "Черновик отчета"]
        for title in photo_titles:
            photo = Photo.objects.create(
                user=random.choice(users),
                title=title,
                file=self.generate_dummy_image(f"{title.replace(' ', '_')}.jpg")
            )
            photos.append(photo)

        # 7. Фотоальбомы (10 штук)
        album_titles = [
            "Поездка в Осаку", "Коллекция карточек Pokémon", "MEGA Dream ex открытие", 
            "Хакатон Московского Политеха", "Курсач по веб-разработке", "Проекты на Go и React", 
            "Заметки по IDEF0 и DFD", "Турнир в Фукуоке", "Архив репозиториев", "Летняя практика"
        ]
        albums = []
        for title in album_titles:
            album = PhotoAlbum.objects.create(
                title=title,
                description=f"Описание для альбома {title}",
                user=random.choice(users),
                cover_type=random.choice(covers),
                status=random.choice(['Draft', 'Printing', 'Completed'])
            )
            albums.append(album)

        # 8. Страницы и размещения (Минимум 10 страниц и 10 фото на них)
        for album in albums:
            # Создаем 2 страницы для каждого альбома (итого 20 страниц)
            for page_num in range(1, 3):
                page = AlbumPage.objects.create(album=album, page_number=page_num)
                # Размещаем 1 случайное фото на каждой странице
                PhotoPlacement.objects.create(
                    photo=random.choice(photos),
                    page=page,
                    x_position=random.uniform(0, 100),
                    y_position=random.uniform(0, 100),
                    scale=random.uniform(0.5, 2.0)
                )

        # 9. Старые модели Project, Order, OrderItem (по 10 штук)
        projects = []
        for i in range(10):
            project = Project.objects.create(
                user=random.choice(users),
                format=random.choice(formats),
                title=f"Устаревший проект #{i}",
                status=random.choice(['Draft', 'Ready'])
            )
            projects.append(project)

        for i in range(10):
            order = Order.objects.create(
                user=random.choice(users),
                total_amount=random.randint(1000, 15000),
                status=random.choice(['Created', 'Paid', 'Printed', 'Shipped'])
            )
            
            # Выбираем 1-2 УНИКАЛЬНЫХ проекта для этого заказа
            selected_projects = random.sample(projects, random.randint(1, 2))
            
            for project in selected_projects:
                OrderItem.objects.create(
                    order=order,
                    project=project,
                    quantity=random.randint(1, 5),
                    price_at_moment=random.randint(500, 3000)
                )

        self.stdout.write(self.style.SUCCESS("Успех! База данных заполнена. Создано минимум по 10 записей во всех таблицах."))