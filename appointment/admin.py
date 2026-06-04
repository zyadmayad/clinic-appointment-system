from django.contrib import admin
from appointment.models import Appointment, AppointmentHistory

admin.site.register(Appointment)
admin.site.register(AppointmentHistory)

