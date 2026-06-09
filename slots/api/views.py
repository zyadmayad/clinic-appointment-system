from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from appointment.models import Appointment
from schedule.models import Schedule
from slots.api.serializer import SlotSerializer, SlotUpdateSerializer
from slots.models import Slot
from slots.utils import coerce_time, ranges_overlap_same_day


def _validate_slot_intervals(schedule_date, parsed_slots):
  
    for i, (s, e) in enumerate(parsed_slots):
        if s >= e:
            return 'Each slot must have start_time strictly before end_time.'
        for j in range(i + 1, len(parsed_slots)):
            s2, e2 = parsed_slots[j]
            if ranges_overlap_same_day(schedule_date, s, e, s2, e2):
                return (
                    'Slots cannot overlap or duplicate. '
                    'A new slot must not fall inside or between existing slots for this day.'
                )
    return None


@api_view(['GET'])
def slot_list(request, doctor_id):
    date = request.query_params.get('date')
    qs = Slot.objects.filter(doctor_id=doctor_id).order_by('date', 'start_time')
    if date:
        qs = qs.filter(date=date)

    serializer = SlotSerializer(qs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def slot_create(request):
    slots_data = request.data.get('slots', [])
    doctor_id = request.data.get('doctor')
    schedule_id = request.data.get('schedule')

    if not doctor_id or not schedule_id:
        return Response({'detail': 'doctor and schedule are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        doctor_id_int = int(doctor_id)
    except (TypeError, ValueError):
        return Response({'detail': 'Invalid doctor id.'}, status=status.HTTP_400_BAD_REQUEST)

    if doctor_id_int != request.user.id:
        return Response({'detail': 'You can only create slots for your own account.'}, status=status.HTTP_403_FORBIDDEN)

    if not isinstance(slots_data, list) or not slots_data:
        return Response({'detail': 'slots must be a non-empty list'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        schedule = Schedule.objects.get(id=schedule_id, doctor_id=doctor_id_int)
    except Schedule.DoesNotExist:
        return Response({'detail': 'Schedule not found for this doctor'}, status=status.HTTP_404_NOT_FOUND)

    parsed_slots = []
    for slot_info in slots_data:
        try:
            start_time = coerce_time(slot_info.get('start_time'))
            end_time = coerce_time(slot_info.get('end_time'))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        parsed_slots.append((start_time, end_time))

    err = _validate_slot_intervals(schedule.date, parsed_slots)
    if err:
        return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)

    existing = Slot.objects.filter(doctor_id=doctor_id_int, date=schedule.date)
    for start_time, end_time in parsed_slots:
        for ex in existing:
            if ranges_overlap_same_day(
                schedule.date,
                start_time,
                end_time,
                ex.start_time,
                ex.end_time,
            ):
                return Response(
                    {
                        'detail': (
                            'Cannot create this slot: it overlaps an existing slot on this day '
                            f'({ex.start_time.strftime("%H:%M")}–{ex.end_time.strftime("%H:%M")}).'
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

    with transaction.atomic():
        created_slots = []
        for start_time, end_time in parsed_slots:
            slot = Slot.objects.create(
                doctor_id=doctor_id_int,
                schedule_id=schedule_id,
                date=schedule.date,
                start_time=start_time,
                end_time=end_time,
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
        return Response({'detail': 'Slot not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = SlotSerializer(slot)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
def slot_update(request, slot_id):
    try:
        slot = Slot.objects.get(id=slot_id)
    except Slot.DoesNotExist:
        return Response({'detail': 'Slot not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = SlotUpdateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.update(slot, serializer.validated_data)
        return Response({'message': 'Slot updated successfully'}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def slot_delete(request, slot_id):
    try:
        slot = Slot.objects.get(pk=slot_id)
    except Slot.DoesNotExist:
        return Response({'detail': 'Slot not found.'}, status=status.HTTP_404_NOT_FOUND)

    if slot.doctor_id != request.user.id:
        return Response({'detail': 'You can only delete your own slots.'}, status=status.HTTP_403_FORBIDDEN)

    if slot.status == 'booked':
        return Response(
            {'detail': 'Cannot delete a booked slot. Cancel the appointment first or contact reception.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    blocking = (
        Appointment.objects.filter(slot=slot)
        .exclude(status='cancelled')
        .exists()
    )
    if blocking:
        return Response(
            {'detail': 'Cannot delete a slot that has an active appointment.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    slot.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
