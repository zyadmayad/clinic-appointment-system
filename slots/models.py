from django.db import models
from django.contrib.auth import get_user_model
from schedule.models import Schedule

User = get_user_model()


class Slot(models.Model):
	STATUS_CHOICES = [
		('available', 'Available'),
		('booked', 'Booked'),
	]

	doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='slots')
	schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='slots')
	date = models.DateField()
	start_time = models.TimeField()
	end_time = models.TimeField()
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')

	def __str__(self):
		return f"{self.doctor} {self.date} {self.start_time}-{self.end_time} ({self.status})"
