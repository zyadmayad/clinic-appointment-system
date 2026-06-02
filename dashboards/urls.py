from django.urls import path
from .import views

app_name = "dashboards"

urlpatterns = [
    path("admin/", views.admin_dashboard, name="admin_dashboard"),
    path("doctor/", views.doctor_dashboard, name="doctor_dashboard"),
    path("receptionist/", views.receptionist_dashboard, name="receptionist_dashboard"),
    path("receptionist/home/", views.reception_home, name="reception_home"),
    path("receptionist/appointments/", views.receptionist_appointments, name="appointments_list"),
    path("receptionist/checkin/", views.receptionist_checkin_queue, name="checkin_queue"),
    path("receptionist/doctor-schedules/", views.receptionist_doctor_schedules, name="doctor_schedules"),
]
