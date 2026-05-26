from django.db import models

class UserRole(models.TextChoices):
    ADMIN = 'admin', 'Administrator'
    DOCTOR = 'doctor', 'Doctor'
    PATIENT = 'patient', 'Patient'
    RECEPTIONIST = 'receptionist', 'Receptionist'


class Users(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.PATIENT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name