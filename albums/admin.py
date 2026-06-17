from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ExportActionModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import (Role, AlbumFormat, User, UserImage, Project, Order, OrderItem,
                     CoverType, Photo, PhotoAlbum, AlbumPage, PhotoPlacement)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)

@admin.register(AlbumFormat)
class AlbumFormatAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'created_by_user', 'created_at')
    list_filter = ('created_at', 'created_by_user')
    search_fields = ('name',)
    raw_id_fields = ('created_by_user',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Использование собственного метода в list_display
    list_display = ('id', 'email', 'first_name', 'last_name', 'role', 'get_email_domain', 'created_at')
    list_display_links = ('id', 'email')
    list_filter = ('role', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('created_at',)
    
    # filter_horizontal работает с ManyToMany полями
    filter_horizontal = ('favorite_formats',)

    # Демонстрация legacy-подхода short_description
    def get_email_domain(self, obj):
        if '@' in obj.email:
            return obj.email.split('@')[1]
        return "-"
    get_email_domain.short_description = 'Домен почты'

@admin.register(UserImage)
class UserImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'file_size_kb', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('user__email',)
    raw_id_fields = ('user',)
    date_hierarchy = 'uploaded_at' # Навигация по датам

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'format', 'status', 'created_at')
    list_display_links = ('id', 'title')
    list_filter = ('status', 'format')
    search_fields = ('title', 'user__email')
    raw_id_fields = ('user', 'format')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'


# INLINES для отображения элементов заказа внутри карточки самого заказа
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1 # Сколько пустых строк выводить
    raw_id_fields = ('project',) # Выбор проекта через виджет поиска ("лупу")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'projects_count', 'created_at')
    list_display_links = ('id', 'user')
    list_filter = ('status',)
    search_fields = ('id', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'updated_by_user')
    date_hierarchy = 'created_at' # Навигация по датам
    
    inlines = [OrderItemInline]

    @admin.display(description='Позиций в заказе', ordering='id')
    def projects_count(self, obj):
        return f"{obj.orderitem_set.count()} шт."


# ==========================================
# АДМИНКА НОВЫХ МОДЕЛЕЙ (ШАГ 2)
# ==========================================

# 1. Настройка ресурса экспорта
class PhotoAlbumResource(resources.ModelResource):
    author_name = fields.Field(column_name='Автор')
    
    class Meta:
        model = PhotoAlbum
        fields = ('id', 'title', 'description', 'status', 'cover_type__name', 'created_at', 'author_name')
        export_order = fields

    def get_export_queryset(self, request):
        # Экспорт только завершенных альбомов
        return super().get_export_queryset(request).filter(status='Completed')

    def dehydrate_created_at(self, album):
        # Кастомный формат даты DD-MM-YYYY
        if album.created_at:
            return album.created_at.strftime('%d-%m-%Y')
        return ''

    def dehydrate_author_name(self, album):
        # Имя Фамилия автора вместо ID (с fallback на email)
        full_name = f"{album.user.first_name or ''} {album.user.last_name or ''}".strip()
        return full_name if full_name else album.user.email


# 2. Inlines для страницы внутри альбома
class AlbumPageInline(admin.TabularInline):
    model = AlbumPage
    extra = 0


# 3. Регистрация Album + подключение истории и экспорта
@admin.register(PhotoAlbum)
class PhotoAlbumAdmin(ExportActionModelAdmin, SimpleHistoryAdmin):
    resource_class = PhotoAlbumResource
    list_display = ('id', 'title', 'user', 'cover_type', 'status', 'pages_count', 'created_at')
    list_filter = ('status', 'cover_type', 'created_at')
    search_fields = ('title', 'description', 'user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user', 'cover_type')
    date_hierarchy = 'created_at'
    inlines = [AlbumPageInline]

    @admin.display(description='Кол-во страниц')
    def pages_count(self, obj):
        return obj.pages.count()

@admin.register(CoverType)
class CoverTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at')
    search_fields = ('name',)

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'created_at')
    raw_id_fields = ('user',)
    search_fields = ('title', 'user__email')