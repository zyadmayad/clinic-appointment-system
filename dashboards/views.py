from django.shortcuts import redirect, render
from auth.permissions import IsAdmin

# Create your views here.
def home(request):
  return render(request, "home.html")

def admin_dashboard(request):
  if not IsAdmin().has_permission(request, None):
    if not request.user.is_authenticated:
      return redirect('auth:login')
    return redirect('home')
  return render(request, "admin_dashboard.html")