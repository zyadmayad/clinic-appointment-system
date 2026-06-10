

from auth.permissions import IsDoctor
from auth.utils import role_required
from schedule.api.serializer import ScheduleExceptionSerializer, ScheduleSerializer
from schedule.models import Schedule
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

@api_view(['GET', 'POST'])

def schedule_list(request,doctor_id):

    if request.method == 'POST':
        try:
            schedule = ScheduleSerializer(data=request.data)
            if schedule.is_valid():
                schedule.save(doctor_id=doctor_id)
                return Response(schedule.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    schedules = Schedule.objects.filter(doctor_id=doctor_id)
    serializer = ScheduleSerializer(schedules, many=True)
    return Response(serializer.data)    


@api_view(['POST'])
@role_required(IsDoctor)
def schedule_exception(request, doctor_id):
    schedule = request.data.get('schedule')

    print(schedule)
    try:
        schedule_obj = Schedule.objects.get(id=schedule, doctor_id=doctor_id)
        schedule_obj.day_type = request.data.get('day_type', 'off')
        schedule_obj.save()
        serializer = ScheduleSerializer(schedule_obj)   
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except Schedule.DoesNotExist:
        return Response({"detail": "Schedule not found."}, status=status.HTTP_404_NOT_FOUND)
    
