from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Project, Photo, PhotoAlbum, AlbumPage, PhotoPlacement

# DRF Импорты
from rest_framework import viewsets, generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

# Наши сериализаторы
from .serializers import (PhotoSerializer, PhotoAlbumSerializer, 
                          AlbumPageSerializer, PhotoPlacementSerializer)

class ProjectListView(ListView):
    model = Project
    template_name = 'albums/project_list.html'
    context_object_name = 'projects'

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'albums/project_detail.html'
    context_object_name = 'project'

class ProjectCreateView(CreateView):
    model = Project
    template_name = 'albums/project_form.html'
    # Поля, доступные пользователю при добавлении
    fields = ['user', 'format', 'title', 'status']

class ProjectUpdateView(UpdateView):
    model = Project
    template_name = 'albums/project_form.html'
    fields = ['user', 'format', 'title', 'status']

class ProjectDeleteView(DeleteView):
    model = Project
    template_name = 'albums/project_confirm_delete.html'
    # При успешном удалении - возвращаем на список проектов
    success_url = reverse_lazy('project_list')


# ==========================================
# REST API VIEWS (ШАГИ 3 И 4)
# ==========================================

# 1. Настройка стандартной пагинации
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    
    # Фильтрация по диапазону дат загрузки через django-filter
    filterset_fields = {'created_at': ['gte', 'lte', 'exact']}

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_authenticated and not self.request.user.is_superuser:
            qs = qs.filter(user=self.request.user)
        return qs

    # СЛОЖНЫЙ ЗАПРОС 2: Фото текущего года без размещений ИЛИ без названия
    @action(methods=['GET'], detail=False)
    def unplaced_or_untitled_this_year(self, request):
        current_year = timezone.now().year
        qs = self.get_queryset().filter(
            Q(created_at__year=current_year) & 
            (Q(photoplacement__isnull=True) | Q(title=''))
        ).distinct()
        
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(qs, many=True).data)


class PhotoAlbumViewSet(viewsets.ModelViewSet):
    serializer_class = PhotoAlbumSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    
    # Фильтрация по GET-параметрам (статус) и SearchFilter (поиск)
    filterset_fields = ['status']
    search_fields = ['title', 'description']

    def get_queryset(self):
        qs = PhotoAlbum.objects.all()
        # Фильтрация альбомов строго по текущему пользователю
        if self.request.user.is_authenticated and not self.request.user.is_superuser:
            qs = qs.filter(user=self.request.user)
        return qs

    # ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ: Получение черновиков
    @action(methods=['GET'], detail=False)
    def drafts(self, request):
        qs = self.get_queryset().filter(status='Draft')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)

    # СЛОЖНЫЙ ЗАПРОС 1: Свадебные альбомы вне кожи
    @action(methods=['GET'], detail=False)
    def wedding_non_leather(self, request):
        qs = self.get_queryset().filter(
            Q(title__icontains='Свадьба') & 
            Q(status='Completed') & 
            ~Q(cover_type__name__icontains='Кожа')
        ).distinct()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(qs, many=True).data)

    # ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ: Клонирование альбома
    @action(methods=['POST'], detail=True)
    def clone(self, request, pk=None):
        album = self.get_object()
        
        # Копируем сам альбом
        new_album = PhotoAlbum.objects.create(
            title=f"{album.title} (Копия)",
            description=album.description,
            user=album.user,
            cover_type=album.cover_type,
            status='Draft' # Логично, что копия всегда становится черновиком
        )
        
        # Глубокое копирование: Страницы и Размещения фотографий
        for page in album.pages.all():
            new_page = AlbumPage.objects.create(album=new_album, page_number=page.page_number)
            for placement in page.placements.all():
                PhotoPlacement.objects.create(
                    photo=placement.photo,
                    page=new_page,
                    x_position=placement.x_position,
                    y_position=placement.y_position,
                    scale=placement.scale
                )
                
        serializer = self.get_serializer(new_album)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# Фильтр по именованным аргументам в URL: альбомы по типу обложки
class AlbumsByCoverTypeView(generics.ListAPIView):
    serializer_class = PhotoAlbumSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        cover_id = self.kwargs.get('cover_id')
        qs = PhotoAlbum.objects.filter(cover_type_id=cover_id)
        if self.request.user.is_authenticated and not self.request.user.is_superuser:
            qs = qs.filter(user=self.request.user)
        return qs