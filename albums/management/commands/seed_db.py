"""
Команда для заполнения базы данных тестовыми данными.
Использование: python manage.py seed_db
"""
import os
import random
from io import BytesIO
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
from albums.models import CoverType, Photo, PhotoAlbum, AlbumPage, PhotoPlacement, UserProfile


def create_placeholder_image(width=800, height=600, color=None, label="Photo"):
    """Создаёт простое цветное изображение-заглушку."""
    if color is None:
        color = (
            random.randint(80, 220),
            random.randint(80, 220),
            random.randint(80, 220),
        )
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    # Рамка
    draw.rectangle([10, 10, width - 10, height - 10], outline=(255, 255, 255), width=3)
    # Надпись по центру
    text = label
    bbox = draw.textbbox((0, 0), text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((width - tw) / 2, (height - th) / 2), text, fill=(255, 255, 255))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    return buf


class Command(BaseCommand):
    help = "Заполняет базу данных тестовыми данными"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистить базу данных перед заполнением",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("🗑️  Очистка базы данных...")
            PhotoPlacement.objects.all().delete()
            AlbumPage.objects.all().delete()
            PhotoAlbum.objects.all().delete()
            Photo.objects.all().delete()
            CoverType.objects.all().delete()
            UserProfile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("   База очищена."))

        # ── 1. Типы обложек ──────────────────────────────────────────────
        self.stdout.write("📚 Создание типов обложек...")
        cover_types_data = [
            {"name": "Мягкая обложка", "description": "Экономичный вариант из плотной бумаги", "price": "499.00"},
            {"name": "Твёрдая обложка", "description": "Классическая твёрдая обложка из картона", "price": "899.00"},
            {"name": "Кожаная обложка", "description": "Премиум-обложка из натуральной кожи", "price": "2499.00"},
            {"name": "Льняная обложка", "description": "Текстильная обложка из натурального льна", "price": "1299.00"},
            {"name": "Обложка с фото", "description": "Обложка с печатью фотографии", "price": "699.00"},
        ]
        cover_types = []
        for ct_data in cover_types_data:
            ct, created = CoverType.objects.get_or_create(name=ct_data["name"], defaults=ct_data)
            cover_types.append(ct)
        self.stdout.write(self.style.SUCCESS(f"   Создано типов обложек: {len(cover_types)}"))

        # ── 2. Пользователи ──────────────────────────────────────────────
        self.stdout.write("👥 Создание пользователей...")
        users_data = [
            {"username": "anna_ivanova", "first_name": "Анна", "last_name": "Иванова", "email": "anna@example.com"},
            {"username": "petr_smirnov", "first_name": "Пётр", "last_name": "Смирнов", "email": "petr@example.com"},
            {"username": "maria_kozlova", "first_name": "Мария", "last_name": "Козлова", "email": "maria@example.com"},
        ]
        users = []
        for ud in users_data:
            user, created = User.objects.get_or_create(
                username=ud["username"],
                defaults={**ud, "password": "pbkdf2_sha256$dummy"},
            )
            if created:
                user.set_password("password123")
                user.save()
            # Профиль
            UserProfile.objects.get_or_create(
                user=user,
                defaults={"bio": f"Любитель фотографии. Пользователь: {user.get_full_name()}"},
            )
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f"   Создано пользователей: {len(users)}"))

        # ── 3. Фотографии ────────────────────────────────────────────────
        self.stdout.write("🖼️  Создание фотографий...")
        colors = [
            (220, 100, 100), (100, 180, 100), (100, 120, 220),
            (220, 180, 60),  (180, 100, 220), (60, 180, 200),
            (220, 140, 60),  (160, 220, 100), (220, 80, 160),
        ]
        all_photos = []
        photo_counter = 1
        for user in users:
            for i in range(6):
                label = f"Фото {photo_counter}"
                color = colors[(photo_counter - 1) % len(colors)]
                img_buf = create_placeholder_image(
                    width=random.choice([800, 1024, 1200]),
                    height=random.choice([600, 768, 900]),
                    color=color,
                    label=label,
                )
                photo = Photo(
                    user=user,
                    title=label,
                    width=800,
                    height=600,
                    size=img_buf.getbuffer().nbytes,
                )
                filename = f"seed_photo_{photo_counter}.jpg"
                photo.file.save(filename, ContentFile(img_buf.read()), save=True)
                all_photos.append(photo)
                photo_counter += 1
        self.stdout.write(self.style.SUCCESS(f"   Создано фотографий: {len(all_photos)}"))

        # ── 4. Фотоальбомы ───────────────────────────────────────────────
        self.stdout.write("📖 Создание фотоальбомов...")
        albums_data = [
            # Anna
            {"user": users[0], "title": "Свадьба Анны и Дмитрия", "status": "completed", "cover_type": cover_types[2]},
            {"user": users[0], "title": "Летний отпуск 2024",      "status": "printing",  "cover_type": cover_types[1]},
            {"user": users[0], "title": "Новогодний альбом",        "status": "draft",     "cover_type": None},
            # Petr
            {"user": users[1], "title": "Горный поход",             "status": "in_progress", "cover_type": cover_types[0]},
            {"user": users[1], "title": "Выпускной 2024",           "status": "delivered", "cover_type": cover_types[3]},
            # Maria
            {"user": users[2], "title": "День рождения мамы",       "status": "completed", "cover_type": cover_types[4]},
            {"user": users[2], "title": "Путешествие в Сочи",       "status": "draft",     "cover_type": None},
        ]
        albums = []
        for ad in albums_data:
            album, created = PhotoAlbum.objects.get_or_create(
                title=ad["title"],
                user=ad["user"],
                defaults={
                    "status": ad["status"],
                    "cover_type": ad["cover_type"],
                    "description": f"Описание альбома «{ad['title']}»",
                },
            )
            albums.append(album)
        self.stdout.write(self.style.SUCCESS(f"   Создано альбомов: {len(albums)}"))

        # ── 5. Страницы и размещения ─────────────────────────────────────
        self.stdout.write("📄 Создание страниц и размещений фото...")
        placements_total = 0
        for album in albums:
            user_photos = [p for p in all_photos if p.user == album.user]
            num_pages = random.randint(2, 4)
            for page_num in range(1, num_pages + 1):
                page, _ = AlbumPage.objects.get_or_create(
                    album=album,
                    page_number=page_num,
                    defaults={"width": 210, "height": 297},
                )
                # 1–3 фото на страницу
                photos_for_page = random.sample(user_photos, min(random.randint(1, 3), len(user_photos)))
                existing = PhotoPlacement.objects.filter(page=page).values_list("photo_id", flat=True)
                for idx, photo in enumerate(photos_for_page):
                    if photo.id in existing:
                        continue
                    PhotoPlacement.objects.create(
                        photo=photo,
                        page=page,
                        x=round(10 + idx * 65, 1),
                        y=round(10 + random.uniform(0, 30), 1),
                        width=round(random.uniform(50, 90), 1),
                        height=round(random.uniform(40, 70), 1),
                        rotation=round(random.uniform(0, 15), 1),
                        z_index=idx,
                    )
                    placements_total += 1
        self.stdout.write(self.style.SUCCESS(f"   Создано страниц и размещений: {placements_total}"))

        # ── Итог ──────────────────────────────────────────────────────────
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("✅ База данных успешно заполнена!"))
        self.stdout.write(f"   Типы обложек : {CoverType.objects.count()}")
        self.stdout.write(f"   Пользователи : {User.objects.filter(is_superuser=False).count()}")
        self.stdout.write(f"   Фотографии   : {Photo.objects.count()}")
        self.stdout.write(f"   Альбомы      : {PhotoAlbum.objects.count()}")
        self.stdout.write(f"   Страницы     : {AlbumPage.objects.count()}")
        self.stdout.write(f"   Размещения   : {PhotoPlacement.objects.count()}")
        self.stdout.write("")
        self.stdout.write("🔑 Данные для входа тестовых пользователей:")
        self.stdout.write("   anna_ivanova / password123")
        self.stdout.write("   petr_smirnov / password123")
        self.stdout.write("   maria_kozlova / password123")
