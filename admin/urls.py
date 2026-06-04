from django.urls import path

from .views import admin_dashboard

app_name = "clinic_admin"

urlpatterns = [
    path("", admin_dashboard, name="admin_dashboard"),
]
