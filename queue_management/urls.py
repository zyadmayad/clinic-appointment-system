from django.urls import path

from queue_management.views import CheckInView, QueueManageView, TodayQueueView

urlpatterns = [
    path('check-in/', CheckInView.as_view(), name='queue_check_in'),
    path('today/', TodayQueueView.as_view(), name='queue_today'),
    path('<int:appointment_id>/', QueueManageView.as_view(), name='queue_manage'),
]
