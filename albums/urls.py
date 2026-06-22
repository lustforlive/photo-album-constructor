from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'photos', views.PhotoViewSet, basename='photo')
router.register(r'photo-albums', views.PhotoAlbumViewSet, basename='photoalbum')
router.register(r'cover-types', views.CoverTypeViewSet, basename='covertype')

urlpatterns = [
    path('api/', include(router.urls)),
]