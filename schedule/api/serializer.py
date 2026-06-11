# schedule/api/serializer.py
from rest_framework import serializers
from django.utils import timezone
from datetime import datetime
from schedule.models import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'
        read_only_fields = ['id']

    def validate_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError('date cannot be in the past.')
        return value

    def validate(self, attrs):
        start = attrs.get('start_time', self.instance.start_time if self.instance else None)
        end = attrs.get('end_time', self.instance.end_time if self.instance else None)
        date = attrs.get('date', self.instance.date if self.instance else None)
        session_duration = attrs.get('session_duration', self.instance.session_duration if self.instance else None)

        if start and end and start >= end:
            raise serializers.ValidationError('start_time must be before end_time.')
        
        if session_duration and session_duration <= 0:
            raise serializers.ValidationError('session_duration must be > 0.')
        
        if date and start and end and session_duration:
            total_mins = int((datetime.combine(date, end) - datetime.combine(date, start)).total_seconds() / 60)
            if total_mins % session_duration != 0:
                raise serializers.ValidationError('session_duration must divide the window evenly.')
        
        return attrs


class ScheduleExceptionSerializer(serializers.Serializer):
    schedule = serializers.PrimaryKeyRelatedField(queryset=Schedule.objects.all())

    def validate_schedule(self, value):
        if value.day_type != 'working':
            raise serializers.ValidationError('Cannot add exception to a non-working day.')
        return value

    def create(self, validated_data):
        schedule = validated_data['schedule']
        schedule.day_type = 'off'
        schedule.save()
        return schedule