from urllib import request

from django.shortcuts import redirect, render
from datetime import datetime, timedelta
from schedule.models import Schedule

# Create your views here.
def doctor_schedule(request):
  if not request.user.is_authenticated:
    return redirect('auth:login')
  
  user_name = request.user.username
  id = request.user.id
  
  # Get current week dates starting from Saturday
  today = datetime.now().date()
  saturday = today - timedelta(days=(today.weekday() - 5) % 7)
  friday = saturday + timedelta(days=6)
  
  schedules = Schedule.objects.filter(doctor_id=id,date__gte=saturday,date__lte=friday).order_by('date', 'start_time')

  
  schedule_data = {}
  days_of_week = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
  day_weekday_map = {5: 'Saturday', 6: 'Sunday', 0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday'}
  
  for i, day_name in enumerate(days_of_week):
    day_date = saturday + timedelta(days=i)
    date_str = day_date.strftime('%Y-%m-%d')
    key = f"{day_name} ({date_str})"
    schedule_data[key] = []
  
  for schedule in schedules:
    day_name = day_weekday_map.get(schedule.date.weekday(), 'Unknown')
    date_str = schedule.date.strftime('%Y-%m-%d')
    key = f"{day_name} ({date_str})"
    
    if schedule.day_type == 'working':
      schedule_data[key].append({
          "schedule_id": schedule.id,
          "start": schedule.start_time.strftime('%H:%M'),
          "end": schedule.end_time.strftime('%H:%M'),
          "day_type": "working"
      })
    else:
      schedule_data[key] = [{"day_type": "off"}]

  return render(
      request,
      "doctor/schedules.html",
      {
          "user_name": user_name,
          "schedule_data": schedule_data,
          "week_start": saturday.strftime('%B %d, %Y'),
          "week_end": friday.strftime('%B %d, %Y'),
      },
  )

def patient_queue(request):
  if not request.user.is_authenticated:
    return redirect('auth:login')
  
  user_name = request.user.username
  
  return render(
      request,
      "doctor/patient_queue.html",
      {
          "user_name": user_name,
      },
  )

def consultation(request):
  if not request.user.is_authenticated:
    return redirect('auth:login')
  
  user_name = request.user.username
  
  return render(
      request,
      "doctor/consultation.html",
      {
          "user_name": user_name,
      },
  )