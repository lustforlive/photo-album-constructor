from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'photos', views.PhotoViewSet, basename='photo')
router.register(r'photo-albums', views.PhotoAlbumViewSet, basename='photoalbum')
router.register(r'cover-types', views.CoverTypeViewSet, basename='covertype')

urlpatterns = [
    path('', include(router.urls)),
    path('photo-albums/<int:album_id>/pages/', views.AlbumPageViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='album-pages-list'),
    path('photo-albums/<int:album_id>/pages/<int:pk>/', views.AlbumPageViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='album-pages-detail'),
    path('pages/<int:page_id>/placements/', views.PhotoPlacementViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='page-placements-list'),
    path('pages/<int:page_id>/placements/<int:pk>/', views.PhotoPlacementViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='page-placements-detail'),
]