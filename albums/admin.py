from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    CoverType, Photo, PhotoAlbum, AlbumPage, PhotoPlacement, UserProfile
)


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
class PhotoAlbumAdmin(SimpleHistoryAdmin):
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