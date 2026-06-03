from django.urls import path
from . import views

urlpatterns = [
  path("appointments/", views.admin_appointments, name="admin_appointments"),
  path("doctor-schedules/", views.doctor_schedule, name="doctor_schedule"),
  path("user-managements/", views.user_managements, name="user_managements"),
  path("user-managements/<int:user_id>/role/", views.update_user_role, name="update_user_role"),
  path("user-managements/<int:user_id>/delete/", views.delete_user, name="delete_user"),
]