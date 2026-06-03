from django.contrib import admin
from django.urls import include, path
from auth.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('', include('auth.urls')),
    path('dashboard/', include(('dashboards.urls', 'dashboards'), namespace='dashboards')),
    path('dashboard/doctor/', include(('schedule.urls', 'schedule'), namespace='schedule')),
    path('doctors/', include(('schedule.urls', 'schedule'), namespace='schedule')),
    path('dashboard/patient/', include(('appointment.urls', 'appointment'), namespace='appointment')),
    path('dashboard/admin/', include(('managements.urls', 'managements'), namespace='managements')),
    path('dashboard/receptionist/', include(('receptionist.urls', 'receptionist'), namespace='receptionist')),
    path('api/receptionist/', include('receptionist.api.urls')),
    path('api/doctors/', include('schedule.api.urls')),
    path('api/slots/', include('slots.api.urls')),
    path('api/appointments/', include('appointment.api.urls')),
    path('api/managements/', include('managements.api.urls')),
    path('api/queue/', include('queue_management.api.urls')),
    path('api/', include('auth.api.urls')),
    path("accounts/", include("allauth.urls")),
]
