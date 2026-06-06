from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import serializers

from schedule.api.serializer import ScheduleExceptionSerializer
from schedule.models import Schedule


class ScheduleExceptionSerializerTests(TestCase):
	def setUp(self):
		self.doctor = User.objects.create_user(username='doctor_schedule_exception')

	def test_validate_schedule_rejects_non_working_day(self):
		off_schedule = Schedule.objects.create(
			doctor=self.doctor,
			date=date(2026, 4, 16),
			start_time=time(9, 0),
			end_time=time(12, 0),
			session_duration=30,
			day_type='off',
		)

		serializer = ScheduleExceptionSerializer()
		with self.assertRaisesMessage(
			serializers.ValidationError,
			'Cannot add exception to a non-working day.',
		):
			serializer.validate_schedule(off_schedule)

	def test_create_switches_working_schedule_to_off(self):
		working_schedule = Schedule.objects.create(
			doctor=self.doctor,
			date=date(2026, 4, 17),
			start_time=time(9, 0),
			end_time=time(12, 0),
			session_duration=30,
			day_type='working',
		)

		serializer = ScheduleExceptionSerializer()
		updated_schedule = serializer.create({'schedule': working_schedule})
		self.assertEqual(updated_schedule.day_type, 'off')

