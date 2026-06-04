import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from appointment.models import Appointment, AppointmentHistory
from schedule.models import Schedule


def _make_user(username, **kwargs):
    return User.objects.create_user(username=username, password='pass', **kwargs)


def _make_schedule(doctor, date, start='09:00', end='17:00', session=30):
    return Schedule.objects.create(
        doctor=doctor,
        date=date,
        start_time=start,
        end_time=end,
        session_duration=session,
        day_type='working',
    )


class AppointmentCancelTests(TestCase):
    def setUp(self):
        self.patient = _make_user('patient1')
        self.doctor = _make_user('doctor1')
        self.client = APIClient()
        self.client.force_authenticate(user=self.patient)
        self.apt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=datetime.date(2026, 5, 1),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(9, 30),
            status='requested',
        )

    def test_cancel_requested(self):
        url = reverse('appointment_cancel', args=[self.apt.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.apt.refresh_from_db()
        self.assertEqual(self.apt.status, 'cancelled')
        self.assertTrue(AppointmentHistory.objects.filter(appointment=self.apt, event='cancelled').exists())

    def test_cancel_confirmed(self):
        self.apt.status = 'confirmed'
        self.apt.save()
        url = reverse('appointment_cancel', args=[self.apt.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.apt.refresh_from_db()
        self.assertEqual(self.apt.status, 'cancelled')

    def test_cancel_completed_fails(self):
        self.apt.status = 'completed'
        self.apt.save()
        url = reverse('appointment_cancel', args=[self.apt.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_cancel_other_patient_fails(self):
        other = _make_user('other')
        self.client.force_authenticate(user=other)
        url = reverse('appointment_cancel', args=[self.apt.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class AppointmentConfirmTests(TestCase):
    def setUp(self):
        self.patient = _make_user('patient2')
        self.doctor = _make_user('doctor2')
        self.client = APIClient()
        self.client.force_authenticate(user=self.patient)
        self.apt = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=datetime.date(2026, 5, 1),
            start_time=datetime.time(9, 0),
            end_time=datetime.time(9, 30),
            status='requested',
        )

    def test_confirm_requested(self):
        url = reverse('appointment_confirm', args=[self.apt.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.apt.refresh_from_db()
        self.assertEqual(self.apt.status, 'confirmed')
        self.assertTrue(AppointmentHistory.objects.filter(appointment=self.apt, event='confirmed').exists())

    def test_confirm_already_confirmed_fails(self):
        self.apt.status = 'confirmed'
        self.apt.save()
        url = reverse('appointment_confirm', args=[self.apt.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_confirm_cancelled_fails(self):
        self.apt.status = 'cancelled'
        self.apt.save()
        url = reverse('appointment_confirm', args=[self.apt.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)


class AppointmentBookTests(TestCase):
    def setUp(self):
        self.patient = _make_user('patient3')
        self.doctor = _make_user('doctor3')
        self.client = APIClient()
        self.client.force_authenticate(user=self.patient)
        self.date = datetime.date(2026, 5, 2)
        _make_schedule(self.doctor, self.date)

    def test_book_valid_slot(self):
        url = reverse('appointment_list')
        response = self.client.post(url, {
            'doctor': self.doctor.pk,
            'date': str(self.date),
            'start_time': '09:00',
            'end_time': '09:30',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'requested')
        self.assertTrue(AppointmentHistory.objects.filter(event='booked').exists())

    def test_book_double_booking_fails(self):
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            date=self.date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(9, 30),
            status='confirmed',
        )
        url = reverse('appointment_list')
        response = self.client.post(url, {
            'doctor': self.doctor.pk,
            'date': str(self.date),
            'start_time': '09:00',
            'end_time': '09:30',
        })
        self.assertEqual(response.status_code, 400)

    def test_book_off_day_fails(self):
        Schedule.objects.filter(doctor=self.doctor, date=self.date).update(day_type='off')
        url = reverse('appointment_list')
        response = self.client.post(url, {
            'doctor': self.doctor.pk,
            'date': str(self.date),
            'start_time': '09:00',
            'end_time': '09:30',
        })
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_403(self):
        self.client.force_authenticate(user=None)
        url = reverse('appointment_list')
        response = self.client.post(url, {'doctor': self.doctor.pk})
        self.assertEqual(response.status_code, 403)
