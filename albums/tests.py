from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Photo, PhotoAlbum, CoverType, AlbumPage, PhotoPlacement
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone


# ==========================================
# ТЕСТЫ МОДЕЛЕЙ
# ==========================================

class PhotoAlbumModelTest(TestCase):
    """Тест 1: Модель PhotoAlbum"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.cover_type = CoverType.objects.create(name='Стандартная', price=500)

    def test_album_creation(self):
        """Проверка создания альбома"""
        album = PhotoAlbum.objects.create(
            title='Мой альбом',
            user=self.user,
            cover_type=self.cover_type
        )
        self.assertEqual(album.title, 'Мой альбом')
        self.assertEqual(album.status, 'draft')

    def test_album_str(self):
        """Проверка __str__ метода"""
        album = PhotoAlbum.objects.create(
            title='Тестовый альбом',
            user=self.user,
            cover_type=self.cover_type
        )
        self.assertIn('Тестовый альбом', str(album))

    def test_album_history(self):
        """Проверка история изменений (simple-history)"""
        album = PhotoAlbum.objects.create(
            title='Исходный альбом',
            user=self.user,
            cover_type=self.cover_type
        )
        album.title = 'Измененный альбом'
        album.save()
        
        history = album.history.all()
        self.assertEqual(history.count(), 2)  # 2 версии: создание + изменение


class PhotoModelTest(TestCase):
    """Тест 2: Модель Photo"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_photo_creation(self):
        """Проверка создания фото"""
        photo = Photo.objects.create(
            title='Мое фото',
            user=self.user,
            width=1920,
            height=1080
        )
        self.assertEqual(photo.title, 'Мое фото')
        self.assertEqual(photo.user, self.user)

    def test_photo_filtering(self):
        """Проверка фильтрации фото по пользователю"""
        user2 = User.objects.create_user(username='testuser2', password='12345')
        Photo.objects.create(title='Фото 1', user=self.user)
        Photo.objects.create(title='Фото 2', user=user2)
        
        user1_photos = Photo.objects.filter(user=self.user)
        self.assertEqual(user1_photos.count(), 1)


# ==========================================
# ТЕСТЫ API VIEWS
# ==========================================

class PhotoAlbumAPITest(APITestCase):
    """Тест 3-5: REST API для PhotoAlbum"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='12345')
        self.client.force_authenticate(user=self.user)
        self.cover_type = CoverType.objects.create(name='Обложка', price=500)

    def test_create_album(self):
        """Тест 3: Создание альбома через API"""
        data = {
            'title': 'Новый альбом',
            'description': 'Тестовое описание',
            'cover_type': self.cover_type.id
        }
        response = self.client.post('/api/photo-albums/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PhotoAlbum.objects.count(), 1)

    def test_list_albums(self):
        """Тест 4: Получение списка альбомов"""
        PhotoAlbum.objects.create(
            title='Альбом 1',
            user=self.user,
            cover_type=self.cover_type
        )
        response = self.client.get('/api/photo-albums/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_update_album(self):
        """Тест 5: Обновление альбома"""
        album = PhotoAlbum.objects.create(
            title='Оригинальный альбом',
            user=self.user,
            cover_type=self.cover_type
        )
        data = {'title': 'Измененный альбом'}
        response = self.client.patch(f'/api/photo-albums/{album.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        album.refresh_from_db()
        self.assertEqual(album.title, 'Измененный альбом')

    def test_filter_by_status(self):
        """Тест 6: Фильтрация по статусу"""
        PhotoAlbum.objects.create(
            title='Черновик',
            user=self.user,
            cover_type=self.cover_type,
            status='draft'
        )
        PhotoAlbum.objects.create(
            title='На печати',
            user=self.user,
            cover_type=self.cover_type,
            status='printing'
        )
        response = self.client.get('/api/photo-albums/?status=draft')
        self.assertEqual(len(response.data['results']), 1)

    def test_search_albums(self):
        """Тест 7: Поиск альбомов"""
        PhotoAlbum.objects.create(
            title='Путешествие в Европу',
            user=self.user,
            cover_type=self.cover_type
        )
        response = self.client.get('/api/photo-albums/?search=Европу')
        self.assertEqual(len(response.data['results']), 1)

    def test_clone_album(self):
        """Тест 8: Клонирование альбома"""
        album = PhotoAlbum.objects.create(
            title='Оригинальный',
            user=self.user,
            cover_type=self.cover_type
        )
        response = self.client.post(f'/api/photo-albums/{album.id}/clone/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PhotoAlbum.objects.count(), 2)

    def test_album_validation(self):
        """Тест 9: Валидация альбома"""
        data = {
            'title': 'А',  # Слишком короткое название
            'cover_type': self.cover_type.id
        }
        response = self.client.post('/api/photo-albums/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PhotoAPITest(APITestCase):
    """Тест 10: REST API для Photo"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.force_authenticate(user=self.user)

    def test_list_photos(self):
        """Тест 10: Получение списка фотографий"""
        Photo.objects.create(
            title='Фото 1',
            user=self.user,
            width=1920,
            height=1080
        )
        response = self.client.get('/api/photos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_unused_photos(self):
        """Тест дополнительный: Получение неиспользованных фото"""
        Photo.objects.create(
            title='Неиспользованное фото',
            user=self.user,
            width=1920,
            height=1080
        )
        response = self.client.get('/api/photos/unused_photos/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class CourseworkCriteriaTest(APITestCase):
    """Специфичные тесты для проверки требований ИКТ"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.cover_leather = CoverType.objects.create(name='Кожаная люкс', price=2000)
        self.cover_paper = CoverType.objects.create(name='Бумажная стандарт', price=500)

    def test_completed_wedding_non_leather_filter(self):
        """Проверка Q-запроса 1: завершенные свадебные альбомы НЕ из кожи"""
        self.client.force_authenticate(user=self.user1)
        
        # 1. Завершенный, свадебный, НЕ из кожи (должен быть найден)
        album1 = PhotoAlbum.objects.create(
            title='Наш свадебный день',
            description='Свадебный альбом',
            user=self.user1,
            cover_type=self.cover_paper,
            status='completed'
        )
        
        # 2. Завершенный, свадебный, из кожи (НЕ должен быть найден)
        PhotoAlbum.objects.create(
            title='Свадебный премиум',
            description='Свадебный',
            user=self.user1,
            cover_type=self.cover_leather,
            status='completed'
        )

        # 3. Черновик, свадебный, НЕ из кожи (НЕ должен быть найден)
        PhotoAlbum.objects.create(
            title='Свадебный черновик',
            description='Свадебный',
            user=self.user1,
            cover_type=self.cover_paper,
            status='draft'
        )

        response = self.client.get('/api/photo-albums/completed_wedding_non_leather/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], album1.id)

    def test_unassigned_or_nameless_current_year_filter(self):
        """Проверка Q-запроса 2: нераспределенные или безымянные фото текущего года"""
        self.client.force_authenticate(user=self.user1)

        # 1. Текущий год, без названия, нераспределенная (должна быть найдена)
        photo1 = Photo.objects.create(
            title='',
            user=self.user1
        )
        
        # 2. Текущий год, с названием, распределенная (НЕ должна быть найдена)
        photo2 = Photo.objects.create(
            title='Красивый пейзаж',
            user=self.user1
        )
        album = PhotoAlbum.objects.create(title='Альбом', user=self.user1)
        page = AlbumPage.objects.create(album=album, page_number=1)
        PhotoPlacement.objects.create(photo=photo2, page=page, width=100, height=100)

        response = self.client.get('/api/photos/unassigned_or_nameless_current_year/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], photo1.id)

    def test_idor_page_protection(self):
        """Проверка защиты от IDOR для страниц: пользователь не видит чужие страницы"""
        album_user1 = PhotoAlbum.objects.create(title='Альбом Юзера 1', user=self.user1)
        page_user1 = AlbumPage.objects.create(album=album_user1, page_number=1)

        # Под юзером 2 пытаемся запросить страницы альбома юзера 1
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(f'/api/photo-albums/{album_user1.id}/pages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_placement_user_validation(self):
        """Проверка валидации: нельзя разместить фото другого юзера"""
        album_user1 = PhotoAlbum.objects.create(title='Альбом Юзера 1', user=self.user1)
        page_user1 = AlbumPage.objects.create(album=album_user1, page_number=1)
        photo_user2 = Photo.objects.create(title='Фото Юзера 2', user=self.user2)

        self.client.force_authenticate(user=self.user1)
        data = {
            'photo': photo_user2.id,
            'page': page_user1.id,
            'width': 100,
            'height': 100
        }
        response = self.client.post(f'/api/pages/{page_user1.id}/placements/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)