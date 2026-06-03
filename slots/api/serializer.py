
from rest_framework import serializers

from slots.models import Slot


class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = ['id', 'doctor', 'date', 'start_time', 'end_time', 'status']
        read_only_fields = ['id', 'doctor']


class SlotUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Slot.STATUS_CHOICES)

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()
        return instance
    