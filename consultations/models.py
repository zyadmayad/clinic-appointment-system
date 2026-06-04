from django.db import models

# Create your models here.
class Consultation(models.Model):
    doctor = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    patient = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='patient_consultations')
    appointment = models.ForeignKey('appointment.Appointment', on_delete=models.CASCADE)
    diagnosis = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    prescriptions = models.TextField(blank=True)
    tests = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consultation {self.id} - Dr. {self.doctor.username} with {self.patient.username}"