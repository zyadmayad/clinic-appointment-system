from datetime import date, time, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import serializers

from appointment.api.serializer import (
	_check_no_doctor_overlap,
	_check_no_patient_overlap,
	_validate_slot,
)
from appointment.models import Appointment
from schedule.models import Schedule


class AppointmentCoreTests(TestCase):
	def setUp(self):
		self.doctor = User.objects.create_user(username='doctor_core')
		self.patient = User.objects.create_user(username='patient_core')
		self.target_date = date(2026, 4, 16)

	def test_waiting_time_is_none_when_not_checked_in(self):
		appointment = Appointment.objects.create(
			patient=self.patient,
			doctor=self.doctor,
			date=self.target_date,
			start_time=time(9, 0),
			end_time=time(9, 30),
		)
		self.assertIsNone(appointment.waiting_time)

	def test_waiting_time_returns_timedelta_for_checked_in_appointment(self):
		now = timezone.now()
		appointment = Appointment.objects.create(
			patient=self.patient,
			doctor=self.doctor,
			date=self.target_date,
			start_time=time(9, 0),
			end_time=time(9, 30),
			check_in_time=now - timedelta(minutes=15, seconds=30),
		)

		with patch('appointment.models.timezone.now', return_value=now):
			self.assertEqual(appointment.waiting_time, timedelta(minutes=15, seconds=30))

	def test_validate_slot_raises_when_doctor_has_no_working_schedule(self):
		with self.assertRaisesMessage(
			serializers.ValidationError,
			'Doctor has no working schedule on this date.',
		):
			_validate_slot(self.doctor, self.target_date, time(9, 0), time(9, 30))

	def test_validate_slot_raises_when_end_time_is_not_after_start_time(self):
		Schedule.objects.create(
			doctor=self.doctor,
			date=self.target_date,
			start_time=time(9, 0),
			end_time=time(12, 0),
			session_duration=30,
			day_type='working',
		)
		with self.assertRaisesMessage(
			serializers.ValidationError,
			'end_time must be after start_time.',
		):
			_validate_slot(self.doctor, self.target_date, time(10, 30), time(10, 0))

	def test_validate_slot_raises_when_slot_does_not_match_schedule_constraints(self):
		Schedule.objects.create(
			doctor=self.doctor,
			date=self.target_date,
			start_time=time(9, 0),
			end_time=time(12, 0),
			session_duration=30,
			day_type='working',
		)
		with self.assertRaisesMessage(
			serializers.ValidationError,
			"Requested slot does not fit the doctor's schedule (check times and session duration).",
		):
			_validate_slot(self.doctor, self.target_date, time(9, 0), time(10, 0))

	def test_validate_slot_passes_for_matching_schedule_window_and_duration(self):
		Schedule.objects.create(
			doctor=self.doctor,
			date=self.target_date,
			start_time=time(9, 0),
			end_time=time(12, 0),
			session_duration=30,
			day_type='working',
		)
		_validate_slot(self.doctor, self.target_date, time(9, 30), time(10, 0))

	def test_check_no_doctor_overlap_raises_for_existing_non_cancelled_appointment(self):
		Appointment.objects.create(
			patient=self.patient,
			doctor=self.doctor,
			date=self.target_date,
			start_time=time(9, 0),
			end_time=time(9, 30),
			status='confirmed',
		)
		with self.assertRaisesMessage(
			serializers.ValidationError,
			'This slot is already booked for the doctor.',
		):
			_check_no_doctor_overlap(self.doctor, self.target_date, time(9, 0))

	def test_check_no_patient_overlap_raises_for_overlapping_time_range(self):
		Appointment.objects.create(
			patient=self.patient,
			doctor=self.doctor,
			date=self.target_date,
			start_time=time(10, 0),
			end_time=time(10, 30),
			status='confirmed',
		)
		with self.assertRaisesMessage(
			serializers.ValidationError,
			'You already have an appointment during this time slot.',
		):
			_check_no_patient_overlap(self.patient, self.target_date, time(10, 15), time(10, 45))

	def test_overlap_checks_allow_exclude_id_for_reschedule(self):
		appointment = Appointment.objects.create(
			patient=self.patient,
			doctor=self.doctor,
			date=self.target_date,
			start_time=time(10, 0),
			end_time=time(10, 30),
			status='confirmed',
		)
		_check_no_doctor_overlap(
			self.doctor,
			self.target_date,
			time(10, 0),
			exclude_id=appointment.id,
		)
		_check_no_patient_overlap(
			self.patient,
			self.target_date,
			time(10, 5),
			time(10, 20),
			exclude_id=appointment.id,
		)
