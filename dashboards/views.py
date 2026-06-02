from django.shortcuts import redirect, render
from django.utils import timezone
from auth.models import Users
from auth.permissions import IsAdmin, IsDoctor
from appointment.models import Appointment

# Create your views here.
def home(request):
  return render(request, "home.html")

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