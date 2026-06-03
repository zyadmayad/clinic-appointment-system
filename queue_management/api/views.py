from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from appointment.models import Appointment
from queue_management.api.serializers import (
    AppointmentQueueSerializer,
    AppointmentQueueUpdateSerializer,
)
from queue_management.permissions import IsDoctor, IsReceptionist


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsReceptionist])
def check_in(request):
    appointment_id = request.data.get('appointment_id')
    if not appointment_id:
        return Response(
            {'detail': 'appointment_id is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    appointment = get_object_or_404(Appointment, pk=appointment_id)
    if appointment.status == 'checked_in':
        return Response(
            {'detail': 'Appointment is already checked in.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    appointment.status = 'checked_in'
    appointment.check_in_time = timezone.now()
    appointment.save(update_fields=['status', 'check_in_time'])

    serializer = AppointmentQueueSerializer(appointment)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsDoctor])
def today_queue(request):
    today = timezone.localdate()
    appointments = (
        Appointment.objects.filter(date=today, status='checked_in')
        .order_by('check_in_time')
    )
    serializer = AppointmentQueueSerializer(appointments, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsReceptionist])
def queue_manage(request, appointment_id):
    appointment = get_object_or_404(Appointment, pk=appointment_id)
    serializer = AppointmentQueueUpdateSerializer(
        appointment, data=request.data, partial=True
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        AppointmentQueueSerializer(appointment).data,
        status=status.HTTP_200_OK,
    )
