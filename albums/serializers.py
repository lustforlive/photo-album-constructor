from rest_framework import serializers
from .models import CoverType, Photo, PhotoAlbum, AlbumPage, PhotoPlacement

class CoverTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverType
        fields = '__all__'

class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = '__all__'
        read_only_fields = ['user']

    def create(self, validated_data):
        # Автоматически привязываем текущего пользователя при загрузке фото
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)

class PhotoPlacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhotoPlacement
        fields = '__all__'

class AlbumPageSerializer(serializers.ModelSerializer):
    placements = PhotoPlacementSerializer(many=True, read_only=True)

    class Meta:
        model = AlbumPage
        fields = '__all__'

    def validate(self, attrs):
        # ВАЛИДАЦИЯ БИЗНЕС-ЛОГИКИ: не более 8 фотографий на странице
        incoming_placements = self.initial_data.get('placements', [])
        current_count = self.instance.placements.count() if self.instance else 0

        if isinstance(incoming_placements, list) and (current_count + len(incoming_placements)) > 8:
            raise serializers.ValidationError("На одной странице не может быть размещено более 8 фотографий одновременно.")
        
        return attrs

class PhotoAlbumSerializer(serializers.ModelSerializer):
    pages = AlbumPageSerializer(many=True, read_only=True)
    stats = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PhotoAlbum
        fields = '__all__'
        read_only_fields = ['user']

    def get_stats(self, obj):
        # Используем аннотированное поле `pages_count`, если оно есть (иначе fallback на стандартный count)
        pages_count = getattr(obj, 'pages_count', obj.pages.count())
        return f"В альбоме {pages_count} страниц(ы)"

    def validate_title(self, value):
        # ВАЛИДАЦИЯ НА УРОВНЕ ПОЛЯ
        forbidden_words = ['тест', 'спам', 'мат']
        if any(word in value.lower() for word in forbidden_words):
            raise serializers.ValidationError("Название содержит недопустимые слова.")
        return value

    def validate(self, attrs):
        # ВАЛИДАЦИЯ НА УРОВНЕ ОБЪЕКТА
        status = attrs.get('status', self.instance.status if self.instance else 'Draft')
        cover_type = attrs.get('cover_type', self.instance.cover_type if self.instance else None)
        
        if status == 'Completed' and not cover_type:
            raise serializers.ValidationError({"cover_type": "У завершенного альбома должен быть выбран тип обложки."})
        return attrs

    def create(self, validated_data):
        # Передача данных через context: автоматическая привязка автора
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)