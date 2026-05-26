from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache

# Create your views here.
def home(request):
  return render(request, "home.html")

@never_cache
def admin_dashboard(request):
  user_id = request.session.get("user_id")
  user_role = request.session.get("user_role")

  if not user_id or user_role != "admin":
    return redirect("auth:login")

  context = {
    "user_id": user_id,
    "user_name": request.session.get("user_name", "Admin"),
    "user_role": user_role.title(),
    "user_email": request.session.get("user_email", "Admin"),
    "user_detail_api_url": reverse("users_api_detail", args=[user_id]),
  }
  return render(request, "admin_dashboard.html", context)