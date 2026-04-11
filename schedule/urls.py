from django.urls import path

from schedule.api.views import schedule_list
from schedule.views import index, doctor_dashboard, doctor_schedule, patient_queue, consultation

app_name = "schedule"

urlpatterns = [
	path('', index, name='index'),
	path('dashboard/', doctor_dashboard, name='doctor_dashboard'),
	path('schedule/', doctor_schedule, name='doctor_schedule'),
	path('patient-queue/', patient_queue, name='patient_queue'),
	path('consultation/', consultation, name='consultation'),
]