from django.shortcuts import redirect, render
from django.utils import timezone
from datetime import datetime, timedelta
from appointment.models import Appointment
from auth.utils import role_required
from auth.permissions import IsDoctor
from schedule.models import Schedule
from slots.models import Slot

# Create your views here.
@role_required(IsDoctor)
def doctor_schedule(request):
  if not request.user.is_authenticated:
    return redirect('auth:login')
  
  user_name = request.user.username
  id = request.user.id

  # The optional "week" query param is the start date for a 7-day window.
  week_param = request.GET.get('week', '').strip()
  if week_param:
    try:
      anchor_date = datetime.strptime(week_param, '%Y-%m-%d').date()
    except ValueError:
      anchor_date = timezone.localdate()
  else:
    anchor_date = timezone.localdate()

  window_start = anchor_date
  window_end = window_start + timedelta(days=6)

  next_week = window_start + timedelta(days=7)
  
  schedules = Schedule.objects.filter(doctor_id=id,date__gte=window_start,date__lte=window_end).order_by('date', 'start_time')
  slots = Slot.objects.filter(doctor_id=id, date__gte=window_start, date__lte=window_end).order_by('date', 'start_time')

  
  schedule_data = {}
  day_key_by_date = {}
  
  for i in range(7):
    day_date = window_start + timedelta(days=i)
    day_name = day_date.strftime('%A')
    date_str = day_date.strftime('%Y-%m-%d')
    key = f"{day_name} ({date_str})"
    schedule_data[key] = []
    day_key_by_date[day_date] = key
  
  for slot in slots:
    key = day_key_by_date.get(slot.date)

    if not key:
      continue

    schedule_data[key].append({
        "slot_id": slot.id,
        "schedule_id": slot.schedule_id,
        "start": slot.start_time.strftime('%H:%M'),
        "end": slot.end_time.strftime('%H:%M'),
        "day_type": "working",
    })

  off_dates = {schedule.date for schedule in schedules if schedule.day_type == 'off'}
  for off_date in off_dates:
    key = day_key_by_date.get(off_date)
    if key:
      schedule_data[key] = [{"day_type": "off"}]

  return render(
      request,
      "doctor/schedules.html",
      {
          "user_name": user_name,
          "schedule_data": schedule_data,
          "week_start": window_start.strftime('%B %d, %Y'),
          "week_end": window_end.strftime('%B %d, %Y'),
          "selected_week": window_start.strftime('%Y-%m-%d'),
          "next_week": next_week.strftime('%Y-%m-%d'),
      },
  )

@role_required(IsDoctor)
def patient_queue(request):
  if not request.user.is_authenticated:
    return redirect('auth:login')
  
  user_name = request.user.username
  today = timezone.localdate()
  appointments = Appointment.objects.filter(
      doctor=request.user,
      date=today,
      status='checked_in',
  ).order_by('check_in_time')

  queue_items = []
  for appointment in appointments:
    waiting = appointment.waiting_time
    if waiting is None:
      if appointment.status == 'checked_in':
        waiting_display = f"Scheduled {appointment.start_time.strftime('%H:%M')}"
      else:
        waiting_display = 'N/A'
    else:
      hours = waiting.days * 24 + waiting.seconds // 3600
      minutes = (waiting.seconds % 3600) // 60
      waiting_display = f"{hours}h {minutes}m" if hours else f"{minutes}m"

    patient_name = appointment.patient.get_full_name() or appointment.patient.username
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

  return render(
      request,
      "doctor/patient_queue.html",
      {
          "user_name": user_name,
          "queue_items": queue_items,
          "checked_in_count": appointments.count(),
      },
  )