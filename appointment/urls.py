from django.urls import path

from appointment.views import book_appointment, my_appointments, patient_dashboard

app_name = 'appointment'

urlpatterns = [
    path('', patient_dashboard, name='patient_dashboard'),
    path('book/', book_appointment, name='book_appointment'),
    path('my/', my_appointments, name='my_appointments'),
]
