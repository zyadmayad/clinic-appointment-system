from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.ReceptionistDashboardAPIView.as_view(), name='dashboard'),
    path('appointments/', views.ReceptionistAppointmentListAPIView.as_view(), name='appointments'),
    path('requests/', views.ReceptionistPendingRequestsAPIView.as_view(), name='pending_requests'),
    path('requests/<int:pk>/confirm/', views.ConfirmRequestAPIView.as_view(), name='confirm_request'),
    path('checkin/', views.ReceptionistCheckinAPIView.as_view(), name='checkin'),
    path('checkin/<int:pk>/', views.CheckinAppointmentAPIView.as_view(), name='checkin_appointment'),
    path('doctor-schedules/', views.ReceptionistDoctorSchedulesAPIView.as_view(), name='doctor_schedules'),
]
