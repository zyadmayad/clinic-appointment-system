from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth.permissions import IsReceptionist
from appointment.models import Appointment
from receptionist.api.serializers import AppointmentSerializer, ScheduleSerializer
from schedule.models import Schedule


class ReceptionistAPIView(APIView):
    permission_classes = [IsAuthenticated, IsReceptionist]


class ReceptionistDashboardAPIView(ReceptionistAPIView):
    def get(self, request):
        today = timezone.localdate()
        today_appts = Appointment.objects.filter(date=today)
        pending_requests = Appointment.objects.filter(status='requested').order_by('date', 'start_time')
        ready_for_checkin = today_appts.filter(status='confirmed').order_by('start_time')

        return Response({
            'total_today': today_appts.count(),
            'checked_in': today_appts.filter(status='checked_in').count(),
            'awaiting': today_appts.filter(status='confirmed').count(),
            'pending_requests': AppointmentSerializer(pending_requests, many=True).data,
            'ready_for_checkin': AppointmentSerializer(ready_for_checkin, many=True).data,
        })


class ReceptionistAppointmentListAPIView(ReceptionistAPIView):
    def get(self, request):
        search_query = request.query_params.get('q', '').strip()
        selected_status = request.query_params.get('status', '').strip()

        appointments = Appointment.objects.select_related('patient', 'doctor').order_by('date', 'start_time')
        if selected_status:
            appointments = appointments.filter(status=selected_status)

        if search_query:
            appointments = appointments.filter(
                Q(patient__username__icontains=search_query) |
                Q(patient__email__icontains=search_query) |
                Q(doctor__username__icontains=search_query) |
                Q(date__icontains=search_query)
            )

        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)


class ReceptionistPendingRequestsAPIView(ReceptionistAPIView):
    def get(self, request):
        requests_qs = Appointment.objects.filter(status='requested').order_by('date', 'start_time')
        serializer = AppointmentSerializer(requests_qs, many=True)
        return Response(serializer.data)


class ConfirmRequestAPIView(ReceptionistAPIView):
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk, status='requested')
        appointment.status = 'confirmed'
        appointment.save(update_fields=['status'])
        return Response(AppointmentSerializer(appointment).data)


class ReceptionistCheckinAPIView(ReceptionistAPIView):
    def get(self, request):
        today = timezone.localdate()
        waiting_qs = Appointment.objects.filter(status='checked_in').order_by('check_in_time')
        ready_qs = Appointment.objects.filter(status='confirmed', date=today).order_by('start_time')

        return Response({
            'waiting': AppointmentSerializer(waiting_qs, many=True).data,
            'ready_for_checkin': AppointmentSerializer(ready_qs, many=True).data,
        })


class CheckinAppointmentAPIView(ReceptionistAPIView):
    def post(self, request, pk):
        today = timezone.localdate()
        appointment = get_object_or_404(Appointment, pk=pk, status='confirmed', date=today)
        appointment.status = 'checked_in'
        appointment.check_in_time = timezone.now()
        appointment.save(update_fields=['status', 'check_in_time'])
        return Response(AppointmentSerializer(appointment).data)


class ReceptionistDoctorSchedulesAPIView(ReceptionistAPIView):
    def get(self, request):
        doctors_qs = User.objects.filter(users__role='doctor').distinct().order_by('username')
        doctors = [{
            'id': doctor.id,
            'name': doctor.get_full_name() or doctor.username,
            'specialty': 'General Practice',
        } for doctor in doctors_qs]

        selected_doctor_id = request.query_params.get('doctor')
        selected_doctor = next((doctor for doctor in doctors if str(doctor['id']) == selected_doctor_id), None)
        if not selected_doctor:
            selected_doctor = doctors[0] if doctors else {'id': None, 'name': 'No Doctor', 'specialty': ''}

        schedule_records = Schedule.objects.filter(doctor_id=selected_doctor['id']) if selected_doctor and selected_doctor['id'] else Schedule.objects.none()
        week_start = timezone.localdate()
        schedule_days = []
        for day_offset in range(7):
            day = week_start + timedelta(days=day_offset)
            day_records = schedule_records.filter(date=day)
            if day_records.exists():
                shifts = [{
                    'time_range': f"{record.start_time.strftime('%H:%M')} - {record.end_time.strftime('%H:%M')}",
                    'type': record.get_day_type_display(),
                } for record in day_records]
                status = day_records[0].get_day_type_display()
            else:
                shifts = []
                status = 'Off'
            schedule_days.append({
                'name': day.strftime('%A'),
                'date': day.strftime('%b %d'),
                'status': status,
                'shifts': shifts,
            })

        return Response({
            'doctors': doctors,
            'selected_doctor': selected_doctor,
            'schedule_days': schedule_days,
            'week_range': f"{week_start.strftime('%b %d')} — {(week_start + timedelta(days=6)).strftime('%b %d')}",
        })
