from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.
class Schedule(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    session_duration = models.IntegerField()
    day_type = models.CharField(choices=[('working', 'Working Day'), ('off', 'Off Day')], max_length=7)

    def __str__(self):
        return f"{self.doctor} - {self.date} ({self.start_time} to {self.end_time})"