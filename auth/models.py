from django.contrib.auth.models import User
from django.db import models

class Users(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('receptionist', 'Receptionist'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    username = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)