from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from auth.permissions import IsReceptionist
from appointment.models import Appointment
from schedule.models import Schedule


def _receptionist_access_denied(request):
    if not IsReceptionist().has_permission(request, None):
        if not request.user.is_authenticated:
            return redirect('auth:login')
        return redirect('home')
    return None


def receptionist_appointments(request):
    denied = _receptionist_access_denied(request)
    if denied:
        return denied

    search_query = request.GET.get('q', '').strip()
    selected_status = request.GET.get('status', '').strip()

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

    appointment_items = []
    for appointment in appointments:
        patient_name = appointment.patient.get_full_name() or appointment.patient.username
        doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username
        appointment_items.append({
            'patient_name': patient_name,
            'patient_initial': patient_name[:1].upper(),
            'patient_email': appointment.patient.email or '',
            'doctor_name': doctor_name,
            'date': appointment.date.strftime('%b %d, %Y'),
            'start_time': appointment.start_time.strftime('%H:%M'),
            'end_time': appointment.end_time.strftime('%H:%M'),
            'status': appointment.get_status_display(),
            'raw_status': appointment.status,
        })

    return render(request, 'receptionist/appointments_list.html', {
        'user_name': request.user.username,
        'appointments': appointment_items,
        'search_query': search_query,
        'selected_status': selected_status,
    })


def receptionist_checkin_queue(request):
    denied = _receptionist_access_denied(request)
    if denied:
        return denied

    today = timezone.localdate()

    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        if appointment_id:
            appointment = Appointment.objects.filter(id=appointment_id, status='confirmed', date=today).first()
            if appointment:
                appointment.status = 'checked_in'
                appointment.check_in_time = timezone.now()
                appointment.save(update_fields=['status', 'check_in_time'])
        return redirect('receptionist:checkin_queue')

    waiting_qs = Appointment.objects.filter(status='checked_in').order_by('check_in_time')
    ready_qs = Appointment.objects.filter(status='confirmed', date=today).order_by('start_time')

    waiting_items = []
    for appointment in waiting_qs:
        patient_name = appointment.patient.get_full_name() or appointment.patient.username
        waiting_time = appointment.waiting_time
        if waiting_time is None:
            waiting_display = appointment.start_time.strftime('%H:%M')
        else:
            hours = waiting_time.days * 24 + waiting_time.seconds // 3600
            minutes = (waiting_time.seconds % 3600) // 60
            waiting_display = f"{hours}h {minutes}m" if hours else f"{minutes}m"
        waiting_items.append({
            'initial': patient_name[:1].upper(),
            'patient_name': patient_name,
            'check_in_time': appointment.check_in_time.strftime('%H:%M') if appointment.check_in_time else '',
            'waiting_display': waiting_display,
            'doctor_name': appointment.doctor.get_full_name() or appointment.doctor.username,
        })

    ready_items = []
    for appointment in ready_qs:
        patient_name = appointment.patient.get_full_name() or appointment.patient.username
        ready_items.append({
            'id': appointment.id,
            'patient_name': patient_name,
            'start_time': appointment.start_time.strftime('%H:%M'),
            'doctor_name': appointment.doctor.get_full_name() or appointment.doctor.username,
        })

    return render(request, 'receptionist/checkin_queue.html', {
        'user_name': request.user.username,
        'waiting_items': waiting_items,
        'ready_items': ready_items,
    })


def receptionist_doctor_schedules(request):
    denied = _receptionist_access_denied(request)
    if denied:
        return denied

    doctors_qs = User.objects.filter(users__role='doctor').distinct().order_by('username')
    doctors = [{
        'id': doctor.id,
        'name': doctor.get_full_name() or doctor.username,
        'specialty': 'General Practice',
    } for doctor in doctors_qs]

    selected_doctor_id = request.GET.get('doctor')
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

    schedule_notes = [{
        'title': 'Schedule review',
        'message': f"Track {selected_doctor['name']}'s availability and exceptions for this week.",
    }] if selected_doctor else []

    week_range = f"{week_start.strftime('%b %d')} — {(week_start + timedelta(days=6)).strftime('%b %d')}"

    return render(request, 'receptionist/doctor_schedules.html', {
        'user_name': request.user.username,
        'doctors': doctors,
        'selected_doctor': selected_doctor,
        'schedule_days': schedule_days,
        'schedule_notes': schedule_notes,
        'week_range': week_range,
    })
