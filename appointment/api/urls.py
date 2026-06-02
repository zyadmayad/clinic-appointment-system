from django.urls import path

from appointment.api.views import (
    appointment_cancel,
    appointment_confirm,
    appointment_history,
    appointment_list,
    appointment_reschedule,
)

urlpatterns = [
    path('', appointment_list, name='appointment_list'),
    path('<int:appointment_id>/cancel/', appointment_cancel, name='appointment_cancel'),
    path('<int:appointment_id>/confirm/', appointment_confirm, name='appointment_confirm'),
    path('<int:appointment_id>/reschedule/', appointment_reschedule, name='appointment_reschedule'),
    path('<int:appointment_id>/history/', appointment_history, name='appointment_history'),
]
