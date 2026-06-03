from django.contrib.auth.models import User
from rest_framework import serializers

from appointment.models import Appointment
from schedule.models import Schedule


class UserSummarySerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class AppointmentSerializer(serializers.ModelSerializer):
    patient = UserSummarySerializer(read_only=True)
    doctor = UserSummarySerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    appointment_type_display = serializers.CharField(source='get_appointment_type_display', read_only=True)
    waiting_time = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'patient',
            'doctor',
            'date',
            'start_time',
            'end_time',
            'status',
            'status_display',
            'appointment_type',
            'appointment_type_display',
            'check_in_time',
            'waiting_time',
            'created_at',
        ]

    def get_waiting_time(self, obj):
        if obj.waiting_time is None:
            return None
        delta = obj.waiting_time
        hours = delta.days * 24 + delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours}h {minutes}m" if hours else f"{minutes}m"


class ScheduleSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.get_full_name', read_only=True)
    day_type_display = serializers.CharField(source='get_day_type_display', read_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id',
            'doctor',
            'doctor_name',
            'date',
            'start_time',
            'end_time',
            'session_duration',
            'day_type',
            'day_type_display',
        ]
