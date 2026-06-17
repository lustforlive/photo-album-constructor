from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Настраиваем роутер для ViewSets
router = DefaultRouter()
router.register(r'photos', views.PhotoViewSet, basename='photo')
router.register(r'photo-albums', views.PhotoAlbumViewSet, basename='photoalbum')

urlpatterns = [
    # Существующие HTML Views (оставляем для обратной совместимости)
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    
    # REST API endpoints
    path('api/', include(router.urls)),
    
    # Эндпоинт для фильтрации по именованным аргументам URL (Тип обложки)
    path('api/albums/by-cover/<int:cover_id>/', views.AlbumsByCoverTypeView.as_view(), name='albums-by-cover'),
]