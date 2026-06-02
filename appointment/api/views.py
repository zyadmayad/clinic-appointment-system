from django.db.models import Q
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


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def appointment_list(request):
    if request.method == 'POST':
        serializer = BookAppointmentSerializer(data=request.data, context={'patient': request.user})
        if serializer.is_valid():
            data = serializer.validated_data
            appointment = Appointment.objects.create(
                patient=request.user,
                doctor=data['doctor'],
                date=data['date'],
                start_time=data['start_time'],
                end_time=data['end_time'],
                appointment_type=data['appointment_type'],
                status='requested',
            )
            AppointmentHistory.objects.create(appointment=appointment, event='booked')
            return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    qs = Appointment.objects.filter(patient=request.user).select_related('doctor')

    filter_status = request.query_params.get('status')
    if filter_status:
        qs = qs.filter(status=filter_status)

    date = request.query_params.get('date')
    if date:
        qs = qs.filter(date=date)

    date_from = request.query_params.get('date_from')
    if date_from:
        qs = qs.filter(date__gte=date_from)

    date_to = request.query_params.get('date_to')
    if date_to:
        qs = qs.filter(date__lte=date_to)

    search = request.query_params.get('search')
    if search:
        qs = qs.filter(
            Q(doctor__first_name__icontains=search) |
            Q(doctor__last_name__icontains=search) |
            Q(doctor__username__icontains=search)
        )

    qs = qs.order_by('-date', '-start_time')
    serializer = AppointmentSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def appointment_cancel(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, patient=request.user)
    if appointment.status not in ('requested', 'confirmed'):
        return Response(
            {'detail': f'Cannot cancel an appointment with status "{appointment.status}".'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    appointment.status = 'cancelled'
    appointment.save()
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
    appointment.save()
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
    new_detail = f"{data['date']} {data['start_time']}–{data['end_time']}"

    appointment.date = data['date']
    appointment.start_time = data['start_time']
    appointment.end_time = data['end_time']
    appointment.status = 'requested'
    appointment.save()

    AppointmentHistory.objects.create(
        appointment=appointment,
        event='rescheduled',
        detail=f"from {old_detail} to {new_detail}",
    )
    return Response(AppointmentSerializer(appointment).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def appointment_history(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id, patient=request.user)
    history = appointment.history.all()
    serializer = AppointmentHistorySerializer(history, many=True)
    return Response(serializer.data)
