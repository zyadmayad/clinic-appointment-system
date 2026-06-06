from datetime import date, time, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from appointment.models import Appointment
from queue_management.api.serializers import AppointmentQueueSerializer


class AppointmentQueueSerializerTests(TestCase):
	def setUp(self):
		self.patient = User.objects.create_user(username='patient_queue')
		self.doctor = User.objects.create_user(username='doctor_queue')

	def test_get_waiting_time_returns_none_when_check_in_is_missing(self):
		appointment = Appointment.objects.create(
			patient=self.patient,
			doctor=self.doctor,
			date=date(2026, 4, 16),
			start_time=time(9, 0),
			end_time=time(9, 30),
		)

		serialized = AppointmentQueueSerializer(appointment).data
		self.assertIsNone(serialized['waiting_time'])

	def test_get_waiting_time_returns_formatted_duration_dict(self):
		now = timezone.now()
		check_in_time = now - timedelta(hours=1, minutes=2, seconds=3)
		appointment = Appointment.objects.create(
			patient=self.patient,
			doctor=self.doctor,
			date=date(2026, 4, 16),
			start_time=time(10, 0),
			end_time=time(10, 30),
			status='checked_in',
			check_in_time=check_in_time,
		)

		with patch('queue_management.api.serializers.timezone.now', return_value=now):
			waiting_time = AppointmentQueueSerializer(appointment).data['waiting_time']

		self.assertEqual(
			waiting_time,
			{
				'hours': 1,
				'minutes': 2,
				'seconds': 3,
				'total_seconds': 3723,
			},
		)

