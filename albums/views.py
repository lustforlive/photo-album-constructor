from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from django.db.models import Q, Count, Prefetch, F
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .models import Photo, PhotoAlbum, AlbumPage, PhotoPlacement, CoverType
from .serializers import (
    PhotoSerializer, PhotoAlbumSerializer, PhotoAlbumListSerializer,
    AlbumPageSerializer, PhotoPlacementSerializer, CoverTypeSerializer
)


# ==========================================
# ПАГИНАЦИЯ
# ==========================================

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    page_size_max = 100
    page_query_param = 'page'


# ==========================================
# ФИЛЬТРЫ (5 ВАРИАНТОВ)
# ==========================================

class PhotoFilter(django_filters.FilterSet):
    """Фильтр для фотографий"""
    created_at_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = Photo
        fields = ['title', 'created_at_from', 'created_at_to']


class PhotoAlbumFilter(django_filters.FilterSet):
    """Фильтр для альбомов"""
    status = django_filters.ChoiceFilter(choices=PhotoAlbum._meta.get_field('status').choices)
    cover_type = django_filters.ModelChoiceFilter(queryset=CoverType.objects.all())
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    created_at_from = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_at_to = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = PhotoAlbum
        fields = ['status', 'cover_type', 'title', 'created_at_from', 'created_at_to']


# ==========================================
# REST API VIEWSETS
# ==========================================

class PhotoViewSet(viewsets.ModelViewSet):
    """API для управления фотографиями"""
    serializer_class = PhotoSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PhotoFilter
    search_fields = ['title', 'file']
    ordering_fields = ['created_at', 'title', 'size']
    ordering = ['-created_at']

    def get_queryset(self):
        """Оптимизация N+1"""
        return Photo.objects.filter(
            user=self.request.user
        ).select_related('user').prefetch_related('placements').annotate(
            placements_count=Count('placements', distinct=True)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """Автоматическая привязка пользователя"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unassigned_or_nameless_current_year(self, request):
        """
        Получить нераспределенные или безымянные фотографии текущего года
        СЛОЖНЫЙ ЗАПРОС 1: Q-объект с ИЛИ (|) и И (&)
        """
        current_year = timezone.now().year
        qs = self.get_queryset().filter(
            Q(created_at__year=current_year) &
            (Q(placements__isnull=True) | Q(title='') | Q(title__isnull=True))
        ).distinct().order_by('-created_at')

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def unused_photos(self, request):
        """Фотографии, которые не размещены ни на одной странице"""
        qs = self.get_queryset().filter(placements__isnull=True)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Дублирование фотографии"""
        photo = self.get_object()
        new_photo = Photo.objects.create(
            user=request.user,
            title=f"{photo.title} (копия)",
            file=photo.file,
            width=photo.width,
            height=photo.height,
            size=photo.size
        )
        serializer = self.get_serializer(new_photo)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PhotoAlbumViewSet(viewsets.ModelViewSet):
    """API для управления фотоальбомами"""
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PhotoAlbumFilter
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title', 'updated_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Разные сериализаторы для list и detail"""
        if self.action == 'list':
            return PhotoAlbumListSerializer
        return PhotoAlbumSerializer

    def get_queryset(self):
        """
        Оптимизация N+1:
        - select_related для ForeignKey
        - prefetch_related для обратных связей
        - аннотация для подсчета страниц
        """
        queryset = PhotoAlbum.objects.select_related(
            'user', 'cover_type'
        ).prefetch_related(
            Prefetch(
                'pages',
                queryset=AlbumPage.objects.prefetch_related(
                    'placements__photo'
                ).order_by('page_number')
            )
        ).annotate(
            pages_count=Count('pages', distinct=True)
        )

        # Фильтрация: обычные пользователи видят только свои альбомы
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def perform_create(self, serializer):
        """Автоматическая привязка пользователя"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """
        Клонирование альбома с транзакцией
        Гарантирует, что либо ВСЕ копируется, либо НИЧЕГО
        """
        album = self.get_object()

        try:
            with transaction.atomic():
                # Создаем новый альбом
                new_album = PhotoAlbum.objects.create(
                    user=request.user,
                    title=f"{album.title} (копия)",
                    cover_type=album.cover_type,
                    description=album.description,
                    status='draft'
                )

                # Копируем все страницы и размещения
                for page in album.pages.all():
                    new_page = AlbumPage.objects.create(
                        album=new_album,
                        page_number=page.page_number,
                        width=page.width,
                        height=page.height
                    )

                    # Копируем размещения
                    for placement in page.placements.all():
                        PhotoPlacement.objects.create(
                            page=new_page,
                            photo=placement.photo,
                            x=placement.x,
                            y=placement.y,
                            width=placement.width,
                            height=placement.height,
                            rotation=placement.rotation,
                            z_index=placement.z_index
                        )

                serializer = self.get_serializer(new_album)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Ошибка при клонировании: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def drafts(self, request):
        """Получить все черновики пользователя"""
        qs = self.get_queryset().filter(status='draft')
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def completed_wedding_non_leather(self, request):
        """
        Поиск завершенных свадебных альбомов НЕ из кожи
        СЛОЖНЫЙ ЗАПРОС 2: Q-объект с И (&) и НЕ (~)
        """
        qs = self.get_queryset().filter(
            Q(status='completed') &
            (Q(title__icontains='свадебный') | Q(description__icontains='свадебный')) &
            ~Q(cover_type__name__icontains='кожа')
        ).order_by('-created_at')

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_to_print(self, request, pk=None):
        """Отправить альбом на печать и запустить задачу Celery"""
        album = self.get_object()

        # Проверка готовности
        if album.status == 'delivered':
            return Response(
                {'error': 'Этот альбом уже доставлен'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not album.cover_type:
            return Response(
                {'error': 'Выберите тип обложки перед отправкой на печать'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if album.pages.count() == 0:
            return Response(
                {'error': 'Альбом должен содержать минимум одну страницу'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Обновляем статус
        album.status = 'printing'
        album.save()

        # Запускаем фоновую задачу Celery
        from .tasks import send_printing_email
        send_printing_email.delay(album.id)

        return Response({
            'message': 'Альбом отправлен на печать. Письмо отправляется...',
            'album': self.get_serializer(album).data
        })

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Статистика по альбому"""
        album = self.get_object()
        pages_count = album.pages.count()
        total_photos = PhotoPlacement.objects.filter(page__album=album).count()

        return Response({
            'album_id': album.id,
            'title': album.title,
            'pages_count': pages_count,
            'total_photos': total_photos,
            'status': album.get_status_display(),
            'created_at': album.created_at,
            'updated_at': album.updated_at,
        })


class CoverTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API для типов обложек (только чтение)"""
    queryset = CoverType.objects.all()
    serializer_class = CoverTypeSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]


class AlbumPageViewSet(viewsets.ModelViewSet):
    """API для страниц альбома"""
    serializer_class = AlbumPageSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        album_id = self.kwargs.get('album_id')
        queryset = AlbumPage.objects.filter(album_id=album_id)
        if not self.request.user.is_staff:
            queryset = queryset.filter(album__user=self.request.user)
        return queryset.select_related('album').prefetch_related('placements__photo')


class PhotoPlacementViewSet(viewsets.ModelViewSet):
    """API для размещений фото"""
    serializer_class = PhotoPlacementSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        page_id = self.kwargs.get('page_id')
        queryset = PhotoPlacement.objects.filter(page_id=page_id)
        if not self.request.user.is_staff:
            queryset = queryset.filter(page__album__user=self.request.user)
        return queryset.select_related('photo', 'page')