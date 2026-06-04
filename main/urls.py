from django.contrib import admin
from django.urls import include, path
from auth.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('', include('auth.urls')),
    path('dashboard/', include(('dashboards.urls', 'dashboards'), namespace='dashboards')),
    path('api/', include('auth.api.urls')),
]
