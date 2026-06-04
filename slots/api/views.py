from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from slots.models import Slot
from slots.api.serializer import SlotSerializer, SlotUpdateSerializer
from schedule.models import Schedule

@api_view(['GET'])
def slot_list(request, doctor_id):
    date = request.query_params.get('date')
    if date:
        slots = Slot.objects.filter(date=date, doctor_id=doctor_id)
    else:
        slots = Slot.objects.filter(doctor_id=doctor_id)    

    slots_by_date = {}
    for slot in slots:
        date = str(slot.date)
        if date not in slots_by_date:
            slots_by_date[date] = []
        slots_by_date[date].append({
            'start_time': slot.start_time,
            'end_time': slot.end_time,
            'status': slot.status,
        })

    response_data = [
        {'date': date, 'slots': slots}
        for date, slots in slots_by_date.items()
    ]
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
def slot_create(request):
    slots_data = request.data.get('slots', [])
    doctor_id = request.data.get('doctor')
    schedule_id = request.data.get('schedule')

    if not doctor_id or not schedule_id:
        return Response({'error': 'doctor and schedule are required'}, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(slots_data, list) or not slots_data:
        return Response({'error': 'slots must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        schedule = Schedule.objects.get(id=schedule_id, doctor_id=doctor_id)
    except Schedule.DoesNotExist:
        return Response({'error': 'Schedule not found for this doctor'}, status=status.HTTP_404_NOT_FOUND)

    created_slots = []
    for slot_info in slots_data:
        start_time = slot_info.get('start_time')
        end_time = slot_info.get('end_time')

        if not start_time or not end_time:
            return Response({'error': 'Each slot must include start_time and end_time'}, status=status.HTTP_400_BAD_REQUEST)

        slot = Slot.objects.create(
            doctor_id=doctor_id,
            schedule_id=schedule_id,
            date=schedule.date,
            start_time=start_time,
            end_time=end_time
        )
        created_slots.append(slot)

    return Response(
        {
            'message': 'Slots created successfully',
            'schedule': schedule.id,
            'count': len(created_slots),
        },
        status=status.HTTP_201_CREATED,
    )

@api_view(['GET'])
def slot_detail(request, slot_id):
    try:
        slot = Slot.objects.get(id=slot_id)
    except Slot.DoesNotExist:
        return Response({'error': 'Slot not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = SlotSerializer(slot)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PATCH'])
def slot_update(request, slot_id):
    try:
        slot = Slot.objects.get(id=slot_id)
    except Slot.DoesNotExist:
        return Response({'error': 'Slot not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = SlotUpdateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.update(slot, serializer.validated_data)
        return Response({'message': 'Slot updated successfully'}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def slot_delete(request, slot_id):
    try:
        slot = Slot.objects.get(id=slot_id)
    except Slot.DoesNotExist:
        return Response({'error': 'Slot not found'}, status=status.HTTP_404_NOT_FOUND)

    slot.delete()
    return Response({'message': 'Slot deleted successfully'}, status=status.HTTP_204_NO_CONTENT)