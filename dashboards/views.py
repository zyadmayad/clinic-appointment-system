from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from auth.permissions import IsAdmin, IsDoctor, IsReceptionist
from appointment.models import Appointment
from auth.utils import role_required
from schedule.models import Schedule


# Create your views here.
def home(request):
  return render(request, "home.html")


def _mark_overdue_confirmed_as_no_show(grace_minutes=15):
  now_value = timezone.now()
  if timezone.is_aware(now_value):
    now_value = timezone.localtime(now_value)

  cutoff = now_value - timedelta(minutes=grace_minutes)
  cutoff_date = cutoff.date()
  cutoff_time = cutoff.time().replace(tzinfo=None)

  Appointment.objects.filter(
      status='confirmed',
  ).filter(
      Q(date__lt=cutoff_date) | Q(date=cutoff_date, start_time__lte=cutoff_time)
  ).update(status='no_show')

@role_required(IsAdmin)
def admin_dashboard(request):
  user_name = request.user.username
  role_group = request.user.groups.first()
  user_role = role_group.name if role_group else 'admin'

  total_users = User.objects.count()
  patient_users = User.objects.filter(groups__name='patient').distinct().count()
  doctor_users = User.objects.filter(groups__name='doctor').distinct().count()
  receptionist_users = User.objects.filter(groups__name='receptionist').distinct().count()
  admin_users = User.objects.filter(groups__name='admin').distinct().count()

  total_appointments = Appointment.objects.count()
  appointment_status_counts = {
      status_key: Appointment.objects.filter(status=status_key).count()
      for status_key, _ in Appointment.STATUS_CHOICES
  }

  completed_count = appointment_status_counts.get('completed', 0)
  confirmed_count = appointment_status_counts.get('confirmed', 0)
  checked_in_count = appointment_status_counts.get('checked_in', 0)
  requested_count = appointment_status_counts.get('requested', 0)
  cancelled_count = appointment_status_counts.get('cancelled', 0)
  no_show_count = appointment_status_counts.get('no_show', 0)

  completion_rate = round((completed_count / total_appointments) * 100) if total_appointments else 0
  no_show_rate = round((no_show_count / total_appointments) * 100) if total_appointments else 0

  today = timezone.localdate()
  last_six_days = [today - timedelta(days=index) for index in range(5, -1, -1)]
  weekly_appointment_values = []
  for day in last_six_days:
    weekly_appointment_values.append(Appointment.objects.filter(date=day).count())

  max_weekly_value = max(weekly_appointment_values) if weekly_appointment_values else 0
  weekly_appointment_chart = []
  for day, value in zip(last_six_days, weekly_appointment_values):
    height = int((value / max_weekly_value) * 100) if max_weekly_value else 0
    weekly_appointment_chart.append({
        'label': day.strftime('%a'),
        'value': value,
        'height': max(height, 14) if value else 8,
    })

  recent_appointments_qs = Appointment.objects.select_related('patient', 'doctor').order_by('-created_at')[:5]
  recent_appointments = []
  for appointment in recent_appointments_qs:
    patient_name = appointment.patient.get_full_name() or appointment.patient.username
    doctor_name = appointment.doctor.get_full_name() or appointment.doctor.username
    recent_appointments.append({
        'code': f"APT-{appointment.id:03d}",
        'patient_name': patient_name,
        'doctor_name': doctor_name,
        'status': appointment.get_status_display(),
        'status_key': appointment.status,
        'date': appointment.date.strftime('%b %d, %Y'),
        'time': f"{appointment.start_time.strftime('%H:%M')} - {appointment.end_time.strftime('%H:%M')}",
    })

  return render(
      request,
      "admin/admin_dashboard.html",
      {
          "user_name": user_name,
          "user_role": user_role,
          "total_users": total_users,
          "patient_users": patient_users,
          "doctor_users": doctor_users,
          "receptionist_users": receptionist_users,
          "admin_users": admin_users,
          "total_appointments": total_appointments,
          "completed_count": completed_count,
          "confirmed_count": confirmed_count,
          "checked_in_count": checked_in_count,
          "requested_count": requested_count,
          "cancelled_count": cancelled_count,
          "no_show_count": no_show_count,
          "completion_rate": completion_rate,
          "no_show_rate": no_show_rate,
          "weekly_appointment_chart": weekly_appointment_chart,
          "recent_appointments": recent_appointments,
      },
  )
  
def doctor_dashboard(request):
  if not IsDoctor().has_permission(request, None):
    if not request.user.is_authenticated:
      return redirect('auth:login')
    return redirect('home')

  _mark_overdue_confirmed_as_no_show()

  user_name = request.user.username
  role_group = request.user.groups.first()
  user_role = role_group.name if role_group else 'doctor'
  today = timezone.localdate()

  if request.method == 'POST':
    appointment_id = request.POST.get('appointment_id')
    action = request.POST.get('action')
    if appointment_id and action == 'mark_no_show':
      appointment = Appointment.objects.filter(id=appointment_id,doctor=request.user,status='confirmed',date=today,).first()
      
      if appointment:
        appointment.status = 'no_show'
        appointment.save()

    return redirect('dashboards:doctor_dashboard')

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
      'id': appointment.id,
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
      'id': appointment.id,
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


def receptionist_dashboard(request):
  if not IsReceptionist().has_permission(request, None):
    if not request.user.is_authenticated:
      return redirect('auth:login')
    return redirect('home')

  _mark_overdue_confirmed_as_no_show()

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
    elif appointment_id and action == 'mark_no_show':
      appointment = Appointment.objects.filter(id=appointment_id, status='confirmed', date=today).first()
      if appointment:
        appointment.status = 'no_show'
        appointment.save(update_fields=['status'])
    return redirect('dashboards:receptionist_dashboard')

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

  return render(request, 'receptionist/dashboard.html', {
    'user_name': request.user.username,
    'total_today': total_today,
    'checked_in': checked_in,
    'awaiting': awaiting,
    'pending_requests': pending_requests,
    'pending_requests_count': pending_requests_count,
    'ready_for_checkin': ready_for_checkin,
  })