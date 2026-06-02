from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    TYPE_CHOICES = [
        ('in_person', 'In Person'),
        ('telemedicine', 'Telemedicine'),
    ]

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_as_patient')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments_as_doctor')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    appointment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='in_person')
    check_in_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def waiting_time(self):
        if not self.check_in_time:
            return None
        return timezone.now() - self.check_in_time

    def __str__(self):
        return f"APT-{self.pk:03d} {self.patient} → {self.doctor} on {self.date}"


class AppointmentHistory(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='history')
    event = models.CharField(max_length=20)
    detail = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.event} @ {self.created_at:%Y-%m-%d %H:%M}"
