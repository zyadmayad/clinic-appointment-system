from django.urls import path
from queue_management.api.views import check_in, today_queue, queue_manage

urlpatterns = [
    path('check-in/', check_in, name='queue_check_in'),
    path('today/', today_queue, name='queue_today'),
    path('<int:appointment_id>/', queue_manage, name='queue_manage'),
]
