from django.contrib import admin
from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='homepage'),
    path('admin/', admin.site.urls),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
                        {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
]
