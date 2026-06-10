from django.urls import path
from . import views
from consultations.views import receptionist_summary
app_name = 'receptionist'

urlpatterns = [
    path('appointments/', views.receptionist_appointments, name='appointments_list'),
    path('checkin/', views.receptionist_checkin_queue, name='checkin_queue'),
    path('doctor-schedules/', views.receptionist_doctor_schedules, name='doctor_schedules'),
    path('<int:appointment_id>/summary/', receptionist_summary, name='summary'),
]
