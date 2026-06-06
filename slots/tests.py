from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase

from schedule.models import Schedule
from slots.models import Slot
from slots.utils import book_slot, release_slot, slot_kwargs


class SlotUtilsTests(TestCase):
	def setUp(self):
		self.doctor = User.objects.create_user(username='doctor_slot_utils')
		self.target_date = date(2026, 4, 16)
		self.schedule = Schedule.objects.create(
			doctor=self.doctor,
			date=self.target_date,
			start_time=time(9, 0),
			end_time=time(12, 0),
			session_duration=30,
			day_type='working',
		)

	def _create_slot(self, **overrides):
		data = {
			'doctor': self.doctor,
			'schedule': self.schedule,
			'date': self.target_date,
			'start_time': time(9, 0),
			'end_time': time(9, 30),
			'status': 'available',
		}
		data.update(overrides)
		return Slot.objects.create(**data)

	def test_book_slot_marks_available_slot_as_booked(self):
		slot = self._create_slot()
		booked_slot = book_slot(slot.doctor_id, slot.date, slot.start_time, slot.end_time)
		slot.refresh_from_db()

		self.assertEqual(booked_slot.id, slot.id)
		self.assertEqual(slot.status, 'booked')

	def test_book_slot_raises_for_nonexistent_slot(self):
		with self.assertRaisesMessage(ValueError, 'Requested slot not found. Please pick a valid slot.'):
			book_slot(self.doctor.id, self.target_date, time(11, 0), time(11, 30))

	def test_book_slot_raises_for_already_booked_slot(self):
		slot = self._create_slot(status='booked')
		with self.assertRaisesMessage(ValueError, 'This slot is already booked.'):
			book_slot(slot.doctor_id, slot.date, slot.start_time, slot.end_time)

	def test_release_slot_switches_booked_slot_back_to_available(self):
		slot = self._create_slot(status='booked')
		release_slot(slot.doctor_id, slot.date, slot.start_time, slot.end_time)
		slot.refresh_from_db()
		self.assertEqual(slot.status, 'available')

	def test_slot_kwargs_extracts_expected_fields_from_validated_data_dict(self):
		data = {
			'doctor': self.doctor,
			'date': self.target_date,
			'start_time': time(10, 0),
			'end_time': time(10, 30),
		}

		self.assertEqual(
			slot_kwargs(data),
			{
				'doctor_id': self.doctor.id,
				'date': self.target_date,
				'start_time': time(10, 0),
				'end_time': time(10, 30),
			},
		)

