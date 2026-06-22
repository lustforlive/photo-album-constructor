from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from import_export.resources import ModelResource
from import_export.admin import ExportActionModelAdmin
from .models import (
    CoverType, Photo, PhotoAlbum, AlbumPage, PhotoPlacement, UserProfile
)
from .models import (
    PhotoAlbum, Photo, AlbumPage, PhotoPlacement
)

# Получаем исторические модели
HistoricalPhotoAlbum = PhotoAlbum.history.model
HistoricalPhoto = Photo.history.model
HistoricalAlbumPage = AlbumPage.history.model
HistoricalPhotoPlacement = PhotoPlacement.history.model


@admin.register(HistoricalPhotoAlbum)
class HistoricalPhotoAlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'history_user', 'history_date', 'history_type')
    list_filter = ('history_type', 'status', 'history_date')
    search_fields = ('title', 'history_user__username')
    readonly_fields = [f.name for f in HistoricalPhotoAlbum._meta.get_fields()]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class PhotoAlbumResource(ModelResource):
    class Meta:
        model = PhotoAlbum
        fields = ('id', 'user__username', 'title', 'status', 'created_at')

    def dehydrate_created_at(self, obj):
        return obj.created_at.strftime('%d-%m-%Y %H:%M') if obj.created_at else ''


@admin.register(CoverType)
class CoverTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)


@admin.register(Photo)
class PhotoAdmin(SimpleHistoryAdmin):
    list_display = ('title', 'user', 'width', 'height', 'size', 'created_at')
    search_fields = ('title', 'user__username')
    list_filter = ('created_at', 'user')
    readonly_fields = ('width', 'height', 'size', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'user', 'file')
        }),
        ('Параметры', {
            'fields': ('width', 'height', 'size')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PhotoAlbum)
class PhotoAlbumAdmin(SimpleHistoryAdmin, ExportActionModelAdmin):
    resource_classes = [PhotoAlbumResource]
    list_display = ('title', 'user', 'cover_type', 'status', 'pages_count', 'created_at')
    search_fields = ('title', 'user__username')
    list_filter = ('status', 'cover_type', 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'pages_count')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'user')
        }),
        ('Настройки печати', {
            'fields': ('cover_type', 'status')
        }),
        ('Статистика', {
            'fields': ('pages_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def pages_count(self, obj):
        return obj.pages.count()
    pages_count.short_description = "Количество страниц"


@admin.register(AlbumPage)
class AlbumPageAdmin(SimpleHistoryAdmin):
    list_display = ('album', 'page_number', 'width', 'height', 'placements_count', 'created_at')
    search_fields = ('album__title',)
    list_filter = ('album', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('album', 'page_number')
        }),
        ('Размеры', {
            'fields': ('width', 'height')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def placements_count(self, obj):
        return obj.placements.count()
    placements_count.short_description = "Фотографий на странице"


@admin.register(PhotoPlacement)
class PhotoPlacementAdmin(SimpleHistoryAdmin):
    list_display = ('photo', 'page', 'x', 'y', 'width', 'height', 'z_index', 'created_at')
    search_fields = ('photo__title', 'page__album__title')
    list_filter = ('page__album', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Связи', {
            'fields': ('photo', 'page')
        }),
        ('Позиция и размер', {
            'fields': ('x', 'y', 'width', 'height')
        }),
        ('Трансформация', {
            'fields': ('rotation', 'z_index')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
        }),
        ('Профиль', {
            'fields': ('bio', 'avatar')
        }),
        ('Дата создания', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )