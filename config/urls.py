from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='albums/index.html'), name='home'),  # ← ДОБАВЬТЕ
    path('admin/', admin.site.urls),
    path('api/', include('albums.urls')),
]