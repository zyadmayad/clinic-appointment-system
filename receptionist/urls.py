from django.urls import path
from . import views

app_name = 'receptionist'

urlpatterns = [
    path('appointments/', views.receptionist_appointments, name='appointments_list'),
    path('checkin/', views.receptionist_checkin_queue, name='checkin_queue'),
    path('doctor-schedules/', views.receptionist_doctor_schedules, name='doctor_schedules'),
]
