from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q

# ==========================================
# ОСНОВНЫЕ МОДЕЛИ
# ==========================================

class CoverType(models.Model):
    """Типы обложек для альбомов"""
    name = models.CharField(max_length=100, verbose_name="Название типа обложки", db_index=True)
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Тип обложки"
        verbose_name_plural = "Типы обложек"
        ordering = ['name']
        db_table = 'cover_types'
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} (${self.price})"


class Photo(models.Model):
    """Фотографии пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos', verbose_name="Пользователь")
    title = models.CharField(max_length=255, blank=True, verbose_name="Название фото")
    file = models.ImageField(upload_to='user_photos/%Y/%m/%d/', verbose_name="Файл изображения")
    width = models.IntegerField(default=0, verbose_name="Ширина (px)")
    height = models.IntegerField(default=0, verbose_name="Высота (px)")
    size = models.BigIntegerField(default=0, verbose_name="Размер (байты)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Фотографии"
        ordering = ['-created_at']
        db_table = 'photos'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"Фото: {self.title or self.file.name}"

    def clean(self):
        """Валидация размера файла"""
        from django.core.exceptions import ValidationError
        if self.file.size > 10 * 1024 * 1024:  # 10MB
            raise ValidationError("Максимальный размер файла 10MB")


class PhotoAlbum(models.Model):
    """Фотоальбомы пользователя"""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('in_progress', 'В процессе редактирования'),
        ('completed', 'Завершен'),
        ('printing', 'На печати'),
        ('delivered', 'Доставлен'),
    ]

    title = models.CharField(max_length=255, verbose_name="Название альбома", db_index=True)
    description = models.TextField(blank=True, verbose_name="Описание")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photo_albums', verbose_name="Автор", db_index=True)
    cover_type = models.ForeignKey(CoverType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Тип обложки")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft', verbose_name="Статус", db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Фотоальбом"
        verbose_name_plural = "Фотоальбомы"
        ordering = ['-created_at']
        db_table = 'photo_albums'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def clean(self):
        """Валидация бизнес-логики"""
        from django.core.exceptions import ValidationError
        
        # Валидация 1: Название не может быть пустым
        if not self.title or len(self.title.strip()) < 3:
            raise ValidationError("Название должно содержать минимум 3 символа")
        
        # Валидация 2: Для статуса "printing" должна быть выбрана обложка
        if self.status == 'printing' and not self.cover_type:
            raise ValidationError("Для отправки на печать необходимо выбрать тип обложки")
        
        # Валидация 3: Для статуса "completed" должна быть хотя бы одна страница
        if self.status == 'completed' and self.pages.count() == 0:
            raise ValidationError("Завершенный альбом должен содержать минимум одну страницу")


class AlbumPage(models.Model):
    """Страницы альбома"""
    album = models.ForeignKey(PhotoAlbum, on_delete=models.CASCADE, related_name='pages', verbose_name="Альбом")
    page_number = models.PositiveIntegerField(verbose_name="Номер страницы", validators=[MinValueValidator(1)])
    width = models.FloatField(default=210, verbose_name="Ширина (мм)", validators=[MinValueValidator(100), MaxValueValidator(300)])
    height = models.FloatField(default=297, verbose_name="Высота (мм)", validators=[MinValueValidator(100), MaxValueValidator(300)])
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Страница альбома"
        verbose_name_plural = "Страницы альбомов"
        unique_together = ('album', 'page_number')
        ordering = ['album', 'page_number']
        db_table = 'album_pages'
        indexes = [
            models.Index(fields=['album', 'page_number']),
        ]

    def __str__(self):
        return f"{self.album.title} - Страница {self.page_number}"


class PhotoPlacement(models.Model):
    """Размещение фотографий на странице"""
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='placements', verbose_name="Фотография")
    page = models.ForeignKey(AlbumPage, on_delete=models.CASCADE, related_name='placements', verbose_name="Страница")
    
    x = models.FloatField(default=0, verbose_name="Позиция X (мм)")
    y = models.FloatField(default=0, verbose_name="Позиция Y (мм)")
    width = models.FloatField(verbose_name="Ширина (мм)", validators=[MinValueValidator(10)])
    height = models.FloatField(verbose_name="Высота (мм)", validators=[MinValueValidator(10)])
    rotation = models.FloatField(default=0, verbose_name="Поворот (градусы)", validators=[MinValueValidator(0), MaxValueValidator(360)])
    z_index = models.IntegerField(default=0, verbose_name="Порядок слоев")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Размещение фото"
        verbose_name_plural = "Размещения фото"
        ordering = ['page', 'z_index']
        db_table = 'photo_placements'
        indexes = [
            models.Index(fields=['page']),
            models.Index(fields=['photo']),
        ]

    def __str__(self):
        return f"{self.page} - Фото #{self.photo.id}"

    def clean(self):
        """Валидация размещения"""
        from django.core.exceptions import ValidationError
        
        # Проверка, что фотография принадлежит тому же пользователю, что и альбом
        if self.photo.user != self.page.album.user:
            raise ValidationError("Фотография должна принадлежать автору альбома")


class UserProfile(models.Model):
    """Профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    bio = models.TextField(blank=True, verbose_name="Биография")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Аватар")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания профиля")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Профиль {self.user.username}"