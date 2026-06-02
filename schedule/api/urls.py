from django.urls import path

from schedule.api.views import schedule_list, schedule_exception

urlpatterns = [
	path('<int:doctor_id>/availability', schedule_list, name='schedule-list'),
    path('<int:doctor_id>/exceptions', schedule_exception, name='schedule_exception'),
]