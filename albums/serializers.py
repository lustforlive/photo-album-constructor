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
    class Meta:
        model = PhotoAlbum
        fields = '__all__'