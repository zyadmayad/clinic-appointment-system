from django.utils import timezone
from rest_framework import serializers

from appointment.models import Appointment


class AppointmentQueueSerializer(serializers.ModelSerializer):
    waiting_time = serializers.SerializerMethodField()
    patient = serializers.StringRelatedField()
    doctor = serializers.StringRelatedField()

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
            'check_in_time',
            'waiting_time',
        ]

    def get_waiting_time(self, obj):
        if not obj.check_in_time:
            return None
        delta = timezone.now() - obj.check_in_time
        return {
            'hours': delta.days * 24 + delta.seconds // 3600,
            'minutes': (delta.seconds % 3600) // 60,
            'seconds': delta.seconds % 60,
            'total_seconds': int(delta.total_seconds()),
        }


class AppointmentQueueUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Appointment.STATUS_CHOICES, required=False)

    class Meta:
        model = Appointment
        fields = ['date', 'start_time', 'end_time', 'status', 'check_in_time']
        extra_kwargs = {
            'check_in_time': {'required': False, 'allow_null': True},
        }
