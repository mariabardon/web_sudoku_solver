from django.contrib import admin
from django.urls import path
from django.conf import settings # new
from django.conf.urls.static import static # new

from . import views
urlpatterns = [
    path('', views.index, name='homepage'),
    path('admin/', admin.site.urls),
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]
