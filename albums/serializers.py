from rest_framework import serializers
from django.db.models import Count, Q
from .models import Photo, PhotoAlbum, AlbumPage, PhotoPlacement, CoverType, UserProfile
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)


class UserProfileSerializer(serializers.ModelSerializer):
    """Профиль пользователя"""
    user = UserSerializer(read_only=True)
    albums_count = serializers.SerializerMethodField()
    photos_count = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'bio', 'avatar', 'albums_count', 'photos_count', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_albums_count(self, obj):
        """Количество альбомов пользователя"""
        return obj.user.photo_albums.count()

    def get_photos_count(self, obj):
        """Количество фотографий пользователя"""
        return obj.user.photos.count()


class CoverTypeSerializer(serializers.ModelSerializer):
    """Тип обложки"""
    class Meta:
        model = CoverType
        fields = ('id', 'name', 'description', 'price')
        read_only_fields = ('id',)


class PhotoSerializer(serializers.ModelSerializer):
    """Фотография"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    placements_count = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = ('id', 'title', 'file', 'user', 'user_name', 'width', 'height', 'size', 'placements_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'width', 'height', 'size', 'created_at', 'updated_at')

    def get_placements_count(self, obj):
        """Количество размещений фотографии"""
        return obj.placements.count()

    def validate_title(self, value):
        """Валидация 1: название фото"""
        if value and len(value.strip()) < 2:
            raise serializers.ValidationError("Название должно содержать минимум 2 символа")
        return value

    def validate_file(self, value):
        """Валидация 2: размер файла"""
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise serializers.ValidationError("Максимальный размер файла 10MB")
        return value

    def create(self, validated_data):
        """Автоматическая привязка автора"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PhotoPlacementSerializer(serializers.ModelSerializer):
    """Размещение фото на странице"""
    photo_title = serializers.CharField(source='photo.title', read_only=True)
    photo_url = serializers.URLField(source='photo.file.url', read_only=True)

    class Meta:
        model = PhotoPlacement
        fields = ('id', 'photo', 'photo_title', 'photo_url', 'page', 'x', 'y', 'width', 'height', 'rotation', 'z_index', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_width(self, value):
        """Валидация 3: ширина размещения"""
        if value <= 0 or value > 1000:
            raise serializers.ValidationError("Ширина должна быть от 10 до 1000 мм")
        return value

    def validate_height(self, value):
        """Валидация высоты"""
        if value <= 0 or value > 1000:
            raise serializers.ValidationError("Высота должна быть от 10 до 1000 мм")
        return value

    def validate(self, attrs):
        """Валидация: фотография должна принадлежать автору альбома, и страница должна принадлежать пользователю"""
        photo = attrs.get('photo')
        page = attrs.get('page')
        
        if not photo and self.instance:
            photo = self.instance.photo
        if not page and self.instance:
            page = self.instance.page
            
        if page:
            if page.album.user != self.context['request'].user:
                raise serializers.ValidationError("Вы можете размещать фотографии только на страницах своих альбомов.")
                
        if photo and page:
            if photo.user != page.album.user:
                raise serializers.ValidationError("Выбранная фотография должна принадлежать автору альбома.")
        return attrs


class AlbumPageSerializer(serializers.ModelSerializer):
    """Страница альбома"""
    placements = PhotoPlacementSerializer(many=True, read_only=True)
    placements_count = serializers.SerializerMethodField()

    class Meta:
        model = AlbumPage
        fields = ('id', 'album', 'page_number', 'width', 'height', 'placements', 'placements_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_album(self, value):
        """Проверка, что альбом принадлежит пользователю"""
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("Вы можете создавать страницы только для своих альбомов.")
        return value

    def validate(self, attrs):
        """Валидация: максимум 8 фото на одной странице"""
        incoming = self.initial_data.get('placements', []) if self.initial_data else []
        current = self.instance.placements.count() if self.instance else 0
        if (current + len(incoming)) > 8:
            raise serializers.ValidationError("Превышен лимит: максимум 8 фото на одной странице.")
        return attrs

    def get_placements_count(self, obj):
        """Количество размещений на странице"""
        return obj.placements.count()


class PhotoAlbumSerializer(serializers.ModelSerializer):
    """Фотоальбом с вложенными данными"""
    pages = AlbumPageSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    cover_type_name = serializers.CharField(source='cover_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    pages_count = serializers.SerializerMethodField()
    total_photos = serializers.SerializerMethodField()

    class Meta:
        model = PhotoAlbum
        fields = (
            'id', 'title', 'description', 'user', 'user_name',
            'cover_type', 'cover_type_name', 'status', 'status_display',
            'pages', 'pages_count', 'total_photos',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at', 'pages_count', 'total_photos')

    def get_pages_count(self, obj):
        """Количество страниц"""
        return obj.pages.count()

    def get_total_photos(self, obj):
        """Общее количество фотографий"""
        return PhotoPlacement.objects.filter(page__album=obj).count()

    def validate_title(self, value):
        """Валидация 1: название альбома"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Название должно содержать минимум 3 символа")
        
        # Проверка на дубликаты
        if PhotoAlbum.objects.filter(title=value, user=self.context['request'].user).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("У вас уже есть альбом с таким названием")
        
        return value

    def validate(self, data):
        """Валидация 2-3: бизнес-логика на уровне объекта"""
        # Валидация 2: для печати нужна обложка
        if data.get('status') == 'printing':
            if not data.get('cover_type') and (self.instance and not self.instance.cover_type):
                raise serializers.ValidationError({
                    'cover_type': 'Для отправки на печать необходимо выбрать тип обложки'
                })
        
        # Валидация 3: для завершения нужна хотя бы одна страница
        if data.get('status') == 'completed':
            if self.instance and self.instance.pages.count() == 0:
                raise serializers.ValidationError({
                    'status': 'Завершенный альбом должен содержать минимум одну страницу'
                })
        
        return data

    def create(self, validated_data):
        """Автоматическая привязка автора"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PhotoAlbumListSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для списка альбомов"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    pages_count = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PhotoAlbum
        fields = ('id', 'title', 'user_name', 'status', 'status_display', 'pages_count', 'created_at')
        read_only_fields = fields