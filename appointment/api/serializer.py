from datetime import datetime

from django.contrib.auth import get_user_model
from rest_framework import serializers

from appointment.models import Appointment, AppointmentHistory
from schedule.models import Schedule

User = get_user_model()


class AppointmentHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentHistory
        fields = ['id', 'event', 'detail', 'created_at']


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',
            'date', 'start_time', 'end_time', 'status', 'appointment_type', 'created_at',
        ]
        read_only_fields = ['id', 'patient', 'status', 'created_at']


class BookAppointmentSerializer(serializers.Serializer):
    doctor = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    appointment_type = serializers.ChoiceField(choices=['in_person', 'telemedicine'], default='in_person')

    def validate(self, data):
        _validate_slot(data['doctor'], data['date'], data['start_time'], data['end_time'])
        _check_no_overlap(data['doctor'], data['date'], data['start_time'], data['end_time'])
        return data


class RescheduleAppointmentSerializer(serializers.Serializer):
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    def validate(self, data):
        appointment = self.context.get('appointment')
        _validate_slot(appointment.doctor, data['date'], data['start_time'], data['end_time'])
        _check_no_overlap(
            appointment.doctor, data['date'], data['start_time'], data['end_time'],
            exclude_id=appointment.pk,
        )
        return data


# --- shared validation helpers ---

def _validate_slot(doctor, date, start_time, end_time):
    schedules = Schedule.objects.filter(doctor=doctor, date=date, day_type='working')
    if not schedules.exists():
        raise serializers.ValidationError("Doctor has no working schedule on this date.")

    duration_minutes = int(
        (datetime.combine(date, end_time) - datetime.combine(date, start_time)).total_seconds() / 60
    )
    if duration_minutes <= 0:
        raise serializers.ValidationError("end_time must be after start_time.")

    for sched in schedules:
        slot_fits = start_time >= sched.start_time and end_time <= sched.end_time
        right_duration = duration_minutes == sched.session_duration
        if slot_fits and right_duration:
            return

    raise serializers.ValidationError(
        "Requested slot does not fit the doctor's schedule (check times and session duration)."
    )


def _check_no_overlap(doctor, date, start_time, end_time, exclude_id=None):
    qs = Appointment.objects.filter(
        doctor=doctor,
        date=date,
        start_time=start_time,
    ).exclude(status='cancelled')

    if exclude_id is not None:
        qs = qs.exclude(pk=exclude_id)

    if qs.exists():
        raise serializers.ValidationError("This slot is already booked for the doctor.")
