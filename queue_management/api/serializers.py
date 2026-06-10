from django.utils import timezone
from rest_framework import serializers

from appointment.models import Appointment


class AppointmentQueueSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    patient = serializers.CharField(source='patient.get_full_name', max_length=200, read_only=True)
    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    doctor = serializers.CharField(source='doctor.get_full_name', max_length=200, read_only=True)
    doctor_id = serializers.IntegerField(source='doctor.id', read_only=True)
    date = serializers.DateField(read_only=True)
    start_time = serializers.TimeField(read_only=True)
    end_time = serializers.TimeField(read_only=True)
    status = serializers.CharField(max_length=20, read_only=True)
    check_in_time = serializers.DateTimeField(allow_null=True, read_only=True)
    waiting_time = serializers.SerializerMethodField()

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


class AppointmentQueueUpdateSerializer(serializers.Serializer):
    date = serializers.DateField(required=False)
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
    status = serializers.ChoiceField(choices=Appointment.STATUS_CHOICES, required=False)
    check_in_time = serializers.DateTimeField(required=False, allow_null=True)

    def validate_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("Appointment date cannot be in the past.")
        return value

    def validate_check_in_time(self, value):
        if value is None:
            return value
        if value > timezone.now():
            raise serializers.ValidationError("check_in_time cannot be in the future.")
        return value

    def validate(self, attrs):
        instance = self.instance
        start_time = attrs.get('start_time', instance.start_time if instance else None)
        end_time = attrs.get('end_time', instance.end_time if instance else None)
        status = attrs.get('status', instance.status if instance else None)
        check_in_time = attrs.get('check_in_time', instance.check_in_time if instance else None)

        if start_time is not None and end_time is not None and start_time >= end_time:
            raise serializers.ValidationError({'end_time': 'end_time must be after start_time.'})

        if check_in_time is not None and status not in ('checked_in', 'completed'):
            raise serializers.ValidationError({
                'check_in_time': 'check_in_time can only be set when status is checked_in or completed.'
            })

        return attrs

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AppointmentQueueModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'doctor', 'date', 'start_time', 
            'end_time', 'status', 'check_in_time', 'created_at'
        ]
        read_only_fields = ('id', 'created_at')
