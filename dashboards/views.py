from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from auth.models import Users
from auth.permissions import IsAdmin, IsDoctor, IsReceptionist
from appointment.models import Appointment
from schedule.models import Schedule

# Create your views here.
def _receptionist_access_denied(request):
  if not IsReceptionist().has_permission(request, None):
    if not request.user.is_authenticated:
      return redirect('auth:login')
    return redirect('home')
  return None


def home(request):
  return render(request, "home.html")

def receptionist_dashboard(request):
  denied = _receptionist_access_denied(request)
  if denied:
    return denied
  return redirect('dashboards:reception_home')


def reception_home(request):
  denied = _receptionist_access_denied(request)
  if denied:
    return denied

  today = timezone.localdate()
  if request.method == 'POST':
    appointment_id = request.POST.get('appointment_id')
    action = request.POST.get('action')
    if appointment_id and action == 'confirm_request':
      appointment = Appointment.objects.filter(id=appointment_id, status='requested').first()
      if appointment:
        appointment.status = 'confirmed'
        appointment.save(update_fields=['status'])
    elif appointment_id and action == 'check_in':
      appointment = Appointment.objects.filter(id=appointment_id, status='confirmed', date=today).first()
      if appointment:
        appointment.status = 'checked_in'
        appointment.check_in_time = timezone.now()
        appointment.save(update_fields=['status', 'check_in_time'])
    return redirect('dashboards:reception_home')

  today_appts = Appointment.objects.filter(date=today)

  total_today = today_appts.count()
  checked_in = today_appts.filter(status='checked_in').count()
  awaiting = today_appts.filter(status='confirmed').count()
  pending_requests_qs = Appointment.objects.filter(status='requested').order_by('date', 'start_time')
  pending_requests_count = pending_requests_qs.count()
  ready_for_checkin_qs = today_appts.filter(status='confirmed').order_by('start_time')

  pending_requests = []
  for appointment in pending_requests_qs:
    patient_name = appointment.patient.get_full_name() or appointment.patient.username
    doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username
    pending_requests.append({
      'id': appointment.id,
      'patient_name': patient_name,
      'date': appointment.date.strftime('%b %d'),
      'start_time': appointment.start_time.strftime('%H:%M'),
      'doctor_name': doctor_name,
      'appointment_type': appointment.get_appointment_type_display(),
    })

  ready_for_checkin = []
  for appointment in ready_for_checkin_qs:
    patient_name = appointment.patient.get_full_name() or appointment.patient.username
    ready_for_checkin.append({
      'id': appointment.id,
      'initial': patient_name[:1].upper(),
      'patient_name': patient_name,
      'date': appointment.date.strftime('%b %d'),
      'start_time': appointment.start_time.strftime('%H:%M'),
      'doctor_name': appointment.doctor.get_full_name() or appointment.doctor.username,
    })

  return render(request, "receptionist/dashboard.html", {
      "user_name": request.user.username,
      "total_today": total_today,
      "checked_in": checked_in,
      "awaiting": awaiting,
      "pending_requests": pending_requests,
      "pending_requests_count": pending_requests_count,
      "ready_for_checkin": ready_for_checkin,
  })


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

  return render(request, "receptionist/appointments_list.html", {
      "user_name": request.user.username,
      "appointments": appointment_items,
      "search_query": search_query,
      "selected_status": selected_status,
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
    return redirect('dashboards:checkin_queue')

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

  return render(request, "receptionist/checkin_queue.html", {
      "user_name": request.user.username,
      "waiting_items": waiting_items,
      "ready_items": ready_items,
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

  schedule_notes = []
  if selected_doctor:
    schedule_notes.append({
      'title': 'Schedule review',
      'message': f"Track {selected_doctor['name']}'s availability and exceptions for this week.",
    })

  week_range = f"{week_start.strftime('%b %d')} — {(week_start + timedelta(days=6)).strftime('%b %d')}"

  return render(request, "receptionist/doctor_schedules.html", {
      "user_name": request.user.username,
      "doctors": doctors,
      "selected_doctor": selected_doctor,
      "schedule_days": schedule_days,
      "schedule_notes": schedule_notes,
      "week_range": week_range,
  })


def admin_dashboard(request):
  if not IsAdmin().has_permission(request, None):
    if not request.user.is_authenticated:
      return redirect('auth:login')
    return redirect('home')

  profile = Users.objects.filter(user=request.user).only('role').first()
  user_name = request.user.username
  user_role = profile.role

  return render(
      request,
      "admin/admin_dashboard.html",
      {
          "user_name": user_name,
          "user_role": user_role,
      },
  )
  
def doctor_dashboard(request):
  if not IsDoctor().has_permission(request, None):
    if not request.user.is_authenticated:
      return redirect('auth:login')
    return redirect('home')

  profile = Users.objects.filter(user=request.user).only('role').first()
  user_name = request.user.username
  user_role = profile.role

  today = timezone.localdate()
  appointments_today = Appointment.objects.filter(doctor=request.user, date=today)
  checked_in_count = appointments_today.filter(status='checked_in').count()
  confirmed_count = appointments_today.filter(status='confirmed').count()
  completed_count = appointments_today.filter(status='completed').count()
  no_show_count = appointments_today.filter(status='no_show').count()
  waiting_patients = appointments_today.filter(status='checked_in').order_by('check_in_time')
  upcoming_appointments = appointments_today.filter(status='confirmed').order_by('start_time')

  queue_items = []
  for appointment in waiting_patients:
    patient_name = appointment.patient.get_full_name() or appointment.patient.username
    waiting_time = appointment.waiting_time
    if waiting_time is None:
      if appointment.status == 'checked_in':
        waiting_display = f"Scheduled {appointment.start_time.strftime('%H:%M')}"
      else:
        waiting_display = 'N/A'
    else:
      hours = waiting_time.days * 24 + waiting_time.seconds // 3600
      minutes = (waiting_time.seconds % 3600) // 60
      waiting_display = f"{hours}h {minutes}m" if hours else f"{minutes}m"

    queue_items.append({
      'patient_name': patient_name,
      'patient_initial': patient_name[:1].upper(),
      'display_time': appointment.check_in_time.strftime('%H:%M') if appointment.check_in_time else appointment.start_time.strftime('%H:%M'),
      'waiting_display': waiting_display,
      'status': appointment.get_status_display(),
      'start_time': appointment.start_time.strftime('%H:%M'),
      'end_time': appointment.end_time.strftime('%H:%M'),
    })

  upcoming_items = []
  for appointment in upcoming_appointments:
    patient_name = appointment.patient.get_full_name() or appointment.patient.username
    upcoming_items.append({
      'patient_name': patient_name,
      'start_time': appointment.start_time.strftime('%H:%M'),
      'end_time': appointment.end_time.strftime('%H:%M'),
      'status': appointment.get_status_display(),
    })

  return render(
      request,
      "doctor/doctor-dashboard.html",
      {
          "user_name": user_name,
          "user_role": user_role,
          "today_date": today.strftime('%B %d, %Y'),
          "checked_in_count": checked_in_count,
          "confirmed_count": confirmed_count,
          "completed_count": completed_count,
          "no_show_count": no_show_count,
          "queue_items": queue_items,
          "upcoming_items": upcoming_items,
      },
  )