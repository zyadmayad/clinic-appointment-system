from django.urls import path

from . import views

app_name = 'consultations'

urlpatterns = [
    path('', views.index, name='index'),
    path('appointment/<int:appointment_id>/fill/', views.fill, name='fill'),
    path('appointment/<int:appointment_id>/summary/', views.doctor_summary, name='summary'),
]
