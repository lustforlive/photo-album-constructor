from django.db import models
from django.urls import reverse
from simple_history.models import HistoricalRecords

class Role(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название роли")

    class Meta:
        verbose_name = "Роль"
        verbose_name_plural = "Роли"

    def __str__(self):
        return self.name

class AlbumFormat(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название формата")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Базовая цена")
    created_by_user = models.ForeignKey(
        'User', 
        on_delete=models.PROTECT, 
        related_name='created_formats',
        verbose_name="Кем создано"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Формат альбома"
        verbose_name_plural = "Форматы альбомов"

    def __str__(self):
        return f"{self.name} ({self.base_price} руб.)"

class User(models.Model):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, verbose_name="Роль")
    email = models.EmailField(unique=True, verbose_name="Email")
    first_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Имя")
    last_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Фамилия")
    password_hash = models.CharField(max_length=255, verbose_name="Хэш пароля")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    
    # Добавлено дополнительное поле M2M для демонстрации параметра filter_horizontal в админке
    favorite_formats = models.ManyToManyField(
        AlbumFormat, 
        blank=True, 
        verbose_name="Избранные форматы"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email

class UserImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    image_url = models.URLField(max_length=500, verbose_name="Ссылка на изображение (S3)")
    file_size_kb = models.PositiveIntegerField(null=True, blank=True, verbose_name="Размер файла (КБ)")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Изображение пользователя"
        verbose_name_plural = "Изображения пользователей"

    def __str__(self):
        return f"Фото #{self.pk} (пользователь {self.user.email})"

class Project(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Черновик'),
        ('Ready', 'Готов'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    format = models.ForeignKey(AlbumFormat, on_delete=models.PROTECT, verbose_name="Формат альбома")
    title = models.CharField(max_length=255, default='Мой альбом', verbose_name="Название альбома")
    layout_data = models.JSONField(null=True, blank=True, verbose_name="Разметка (JSON)")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Проект альбома"
        verbose_name_plural = "Проекты альбомов"

    def __str__(self):
        return f"Проект: {self.title} ({self.user.email})"

    def get_absolute_url(self):
        return reverse('project_detail', kwargs={'pk': self.pk})

class Order(models.Model):
    STATUS_CHOICES = [
        ('Created', 'Создан'),
        ('Paid', 'Оплачен'),
        ('Printed', 'Напечатан'),
        ('Shipped', 'Отправлен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name="Клиент")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итоговая сумма")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Created', verbose_name="Статус заказа")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата оформления")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    updated_by_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='updated_orders', 
        verbose_name="Кем обновлен"
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ #{self.pk} на {self.total_amount} руб."

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Заказ")
    project = models.ForeignKey(Project, on_delete=models.PROTECT, verbose_name="Проект альбома")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price_at_moment = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена на момент заказа")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказов"
        unique_together = ('order', 'project')

    def __str__(self):
        return f"{self.quantity} шт. проекта {self.project.title}"


# ==========================================
# НОВЫЕ МОДЕЛИ ДЛЯ ТЗ (ШАГ 1)
# ==========================================

class CoverType(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название типа обложки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Тип обложки"
        verbose_name_plural = "Типы обложек"

    def __str__(self):
        return self.name

class Photo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    title = models.CharField(max_length=255, blank=True, verbose_name="Название фото")
    file = models.ImageField(upload_to='user_photos/', verbose_name="Файл изображения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Фотографии"

    def __str__(self):
        return self.title or f"Фото #{self.pk} ({self.user.email})"

class PhotoAlbum(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Черновик'),
        ('Printing', 'В печати'),
        ('Completed', 'Завершен'),
    ]

    title = models.CharField(max_length=255, verbose_name="Название альбома")
    description = models.TextField(blank=True, verbose_name="Описание")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photo_albums', verbose_name="Автор")
    cover_type = models.ForeignKey(CoverType, on_delete=models.PROTECT, verbose_name="Тип обложки")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft', verbose_name="Статус")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    history = HistoricalRecords() # django-simple-history

    class Meta:
        verbose_name = "Фотоальбом (новый)"
        verbose_name_plural = "Фотоальбомы (новые)"

    def __str__(self):
        return f"Альбом: {self.title} | {self.get_status_display()}"

class AlbumPage(models.Model):
    album = models.ForeignKey(PhotoAlbum, on_delete=models.CASCADE, related_name='pages', verbose_name="Альбом")
    page_number = models.PositiveIntegerField(verbose_name="Номер страницы")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Страница альбома"
        verbose_name_plural = "Страницы альбомов"
        unique_together = ('album', 'page_number')
        ordering = ['album', 'page_number']

    def __str__(self):
        return f"{self.album.title} - Стр. {self.page_number}"

class PhotoPlacement(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, verbose_name="Фотография")
    page = models.ForeignKey(AlbumPage, on_delete=models.CASCADE, related_name='placements', verbose_name="Страница")
    
    # Координаты и масштаб
    x_position = models.FloatField(default=0.0, verbose_name="Позиция X")
    y_position = models.FloatField(default=0.0, verbose_name="Позиция Y")
    scale = models.FloatField(default=1.0, verbose_name="Масштаб")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Размещение фото"
        verbose_name_plural = "Размещения фото"

    def __str__(self):
        return f"Фото #{self.photo_id} на странице #{self.page_id}"