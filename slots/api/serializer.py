# slots/api/serializer.py
from rest_framework import serializers
from slots.models import Slot
from appointment.models import Appointment


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['id', 'doctor', 'date', 'start_time', 'end_time', 'status']
        read_only_fields = ['id', 'doctor']

    def validate(self, attrs):
        if 'start_time' in attrs and 'end_time' in attrs:
            if attrs['start_time'] >= attrs['end_time']:
                raise serializers.ValidationError('start_time must be before end_time.')
        return attrs


class SlotUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Slot.STATUS_CHOICES)

    def validate_status(self, value):
        slot = self.instance
        if slot is None:
            return value
        if slot.status == 'booked' and value != 'booked':
            if Appointment.objects.filter(slot=slot).exclude(
                status__in=['cancelled', 'completed']
            ).exists():
                raise serializers.ValidationError(
                    'Cannot change status while appointment is active.'
                )
        return value

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save(update_fields=['status'])
        return instance