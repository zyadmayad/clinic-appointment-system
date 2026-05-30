from django.urls import path

from schedule.api.views import schedule_list
from schedule.views import index, doctor_dashboard, doctor_schedule

app_name = "schedule"

urlpatterns = [
	path('', index, name='index'),
	path('doctor/dashboard/', doctor_dashboard, name='doctor_dashboard'),
	path('doctor/schedule/', doctor_schedule, name='doctor_schedule'),
]