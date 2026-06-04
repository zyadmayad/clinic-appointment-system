from django.shortcuts import redirect, render
from django.utils import timezone
from datetime import datetime, timedelta
from appointment.models import Appointment
from schedule.models import Schedule
from slots.models import Slot

# Create your views here.
def doctor_schedule(request):
  if not request.user.is_authenticated:
    return redirect('auth:login')
  
  user_name = request.user.username
  id = request.user.id

  # The optional "week" query param can be any date inside the week to show.
  week_param = request.GET.get('week', '').strip()
  if week_param:
    try:
      anchor_date = datetime.strptime(week_param, '%Y-%m-%d').date()
    except ValueError:
      anchor_date = timezone.localdate()
  else:
    anchor_date = timezone.localdate()

  # Get week dates starting from Saturday.
  saturday = anchor_date - timedelta(days=(anchor_date.weekday() - 5) % 7)
  friday = saturday + timedelta(days=6)

  prev_week = saturday - timedelta(days=7)
  next_week = saturday + timedelta(days=7)
  
  schedules = Schedule.objects.filter(doctor_id=id,date__gte=saturday,date__lte=friday).order_by('date', 'start_time')
  slots = Slot.objects.filter(doctor_id=id, date__gte=saturday, date__lte=friday).order_by('date', 'start_time')

  
  schedule_data = {}
  days_of_week = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
  day_weekday_map = {5: 'Saturday', 6: 'Sunday', 0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday'}
  
  for i, day_name in enumerate(days_of_week):
    day_date = saturday + timedelta(days=i)
    date_str = day_date.strftime('%Y-%m-%d')
    key = f"{day_name} ({date_str})"
    schedule_data[key] = []
  
  for slot in slots:
    day_name = day_weekday_map.get(slot.date.weekday(), 'Unknown')
    date_str = slot.date.strftime('%Y-%m-%d')
    key = f"{day_name} ({date_str})"

    schedule_data[key].append({
        "slot_id": slot.id,
        "schedule_id": slot.schedule_id,
        "start": slot.start_time.strftime('%H:%M'),
        "end": slot.end_time.strftime('%H:%M'),
        "day_type": "working",
    })

  off_dates = {schedule.date for schedule in schedules if schedule.day_type == 'off'}
  for off_date in off_dates:
    day_name = day_weekday_map.get(off_date.weekday(), 'Unknown')
    date_str = off_date.strftime('%Y-%m-%d')
    key = f"{day_name} ({date_str})"
    schedule_data[key] = [{"day_type": "off"}]

  return render(
      request,
      "doctor/schedules.html",
      {
          "user_name": user_name,
          "schedule_data": schedule_data,
          "week_start": saturday.strftime('%B %d, %Y'),
          "week_end": friday.strftime('%B %d, %Y'),
          "selected_week": saturday.strftime('%Y-%m-%d'),
          "prev_week": prev_week.strftime('%Y-%m-%d'),
          "next_week": next_week.strftime('%Y-%m-%d'),
      },
  )

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