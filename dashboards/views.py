from django.shortcuts import redirect, render
from auth.models import Users
from auth.permissions import IsAdmin, IsDoctor

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

  return render(
      request,
      "doctor/doctor-dashboard.html",
      {
          "user_name": user_name,
          "user_role": user_role,
      },
  )