from django.shortcuts import redirect, render

# Create your views here.
def index(request):
    return render(request,'admin/admin_dashboard.html')

def doctor_dashboard(request):
  if not request.user.is_authenticated:
    return redirect('auth:login')
  
  user_name = request.user.username
  
  return render(
      request,
      "doctor/doctor-dashboard.html",
      {
          "user_name": user_name,
      },
  )

def doctor_schedule(request):
  if not request.user.is_authenticated:
    return redirect('auth:login')
  
  user_name = request.user.username
  
  schedule_data = {
      "Monday": [{"start": "09:00", "end": "13:00"}, {"start": "14:00", "end": "17:00"}],
      "Tuesday": [{"start": "09:00", "end": "13:00"}],
      "Wednesday": [{"start": "10:00", "end": "14:00"}],
      "Thursday": [{"start": "09:00", "end": "13:00"}, {"start": "14:00", "end": "17:00"}],
      "Friday": [{"start": "09:00", "end": "12:00"}],
      "Saturday": "off",
  }
  
  return render(
      request,
      "doctor/schedules.html",
      {
          "user_name": user_name,
          "schedule_data": schedule_data,
      },
  )