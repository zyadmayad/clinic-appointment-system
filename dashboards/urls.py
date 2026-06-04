from django.urls import path
from .import views

app_name = "dashboards"

urlpatterns = [
    path("admin/", views.admin_dashboard, name="admin_dashboard"),
    path("doctor/", views.doctor_dashboard, name="doctor_dashboard"),
    path("receptionist/", views.receptionist_dashboard, name="receptionist_dashboard"),
]
