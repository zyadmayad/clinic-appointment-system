
from schedule.models import Schedule
from rest_framework import serializers

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = '__all__'
        read_only_fields = ['id']
        
class ScheduleExceptionSerializer(serializers.Serializer):
    schedule = serializers.PrimaryKeyRelatedField(queryset=Schedule.objects.all())
    
    def validate_schedule(self, value):
        if value.day_type != 'working':
            raise serializers.ValidationError("Cannot add exception to a non-working day.")
        return value
    
    def create(self, validated_data):
        schedule = validated_data['schedule']
        schedule.day_type = 'off'
        schedule.save()
        return schedule
