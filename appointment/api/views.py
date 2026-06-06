from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from appointment.models import Appointment, AppointmentHistory
from appointment.api.serializer import (
    AppointmentSerializer,
    AppointmentHistorySerializer,
    BookAppointmentSerializer,
    RescheduleAppointmentSerializer,
)

from slots.utils import book_slot ,slot_kwargs , release_slot





@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def appointment_list(request):
    if request.method == 'POST':
        serializer = BookAppointmentSerializer(data=request.data, context={'patient': request.user})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        with transaction.atomic():
            try:
                slot = book_slot(**slot_kwargs(data))
            except ValueError as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            appointment = Appointment.objects.create(
                patient=request.user, slot=slot,
                doctor=data['doctor'], date=data['date'],
                start_time=data['start_time'], end_time=data['end_time'],
                appointment_type=data['appointment_type'], status='requested',
            )
            AppointmentHistory.objects.create(appointment=appointment, event='booked')

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)

    qs = Appointment.objects.filter(patient=request.user).select_related('doctor')
    p = request.query_params

    if p.get('status'):    qs = qs.filter(status=p['status'])
    if p.get('date'):      qs = qs.filter(date=p['date'])
    if p.get('date_from'): qs = qs.filter(date__gte=p['date_from'])
    if p.get('date_to'):   qs = qs.filter(date__lte=p['date_to'])
    if p.get('search'):
        qs = qs.filter(
            Q(doctor__first_name__icontains=p['search']) |
            Q(doctor__last_name__icontains=p['search']) |
            Q(doctor__username__icontains=p['search'])
        )

    return Response(AppointmentSerializer(qs.order_by('-date', '-start_time'), many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def appointment_cancel(request, appointment_id):
    with transaction.atomic():
        appointment = (
            Appointment.objects.select_for_update()
            .filter(pk=appointment_id, patient=request.user)
            .first()
        )
        if not appointment:
            return Response({'detail': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

        if appointment.status == 'cancelled':
            return Response({'detail': 'This appointment is already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        if appointment.status == 'checked_in':
            return Response(
                {
                    'detail': 'You cannot cancel after you have checked in. Please speak to reception if you need to change your visit.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if appointment.status in ('completed', 'no_show'):
            return Response(
                {'detail': f'Cannot cancel an appointment with status "{appointment.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if appointment.status not in ('requested', 'confirmed'):
            return Response(
                {'detail': f'Cannot cancel an appointment with status "{appointment.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        slot_id = appointment.slot_id
        fallback_release = slot_kwargs(appointment) if not slot_id else None

        appointment.status = 'cancelled'
        appointment.slot = None
        appointment.save(update_fields=['status', 'slot'])

        if slot_id:
            release_slot(slot_id=slot_id)
        else:
            release_slot(**fallback_release)

    AppointmentHistory.objects.create(appointment=appointment, event='cancelled')
    return Response(AppointmentSerializer(appointment).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def appointment_confirm(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, patient=request.user)

    if appointment.status != 'requested':
        return Response(
            {'detail': f'Only a requested appointment can be confirmed (current: "{appointment.status}").'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    appointment.status = 'confirmed'
    appointment.save(update_fields=['status'])
    AppointmentHistory.objects.create(appointment=appointment, event='confirmed')
    return Response(AppointmentSerializer(appointment).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def appointment_reschedule(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, patient=request.user)

    if appointment.status in ('checked_in', 'completed', 'cancelled'):
        return Response(
            {'detail': f'Cannot reschedule an appointment with status "{appointment.status}".'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = RescheduleAppointmentSerializer(data=request.data, context={'appointment': appointment})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    old_detail = f"{appointment.date} {appointment.start_time}–{appointment.end_time}"

    with transaction.atomic():
        try:
            new_slot = book_slot(**slot_kwargs(data))
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        release_slot(**slot_kwargs(appointment))

        appointment.date       = data['date']
        appointment.start_time = data['start_time']
        appointment.end_time   = data['end_time']
        appointment.slot       = new_slot
        appointment.status     = 'requested'
        appointment.save(update_fields=['date', 'start_time', 'end_time', 'slot', 'status'])

    AppointmentHistory.objects.create(
        appointment=appointment, event='rescheduled',
        detail=f"from {old_detail} to {data['date']} {data['start_time']}–{data['end_time']}",
    )
    return Response(AppointmentSerializer(appointment).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appointment_history(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, patient=request.user)
    return Response(AppointmentHistorySerializer(appointment.history.all(), many=True).data)