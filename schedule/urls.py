from django.urls import path

from schedule.api.views import schedule_list
from . import views

app_name = "schedule"

urlpatterns = [
	path('schedule/', views.doctor_schedule, name='doctor_schedule'),
	path('patient-queue/', views.patient_queue, name='patient_queue'),
]