from django.shortcuts import redirect, render
from auth.permissions import IsAdmin, IsDoctor, IsPatient, IsReceptionist
from functools import wraps



def _redirect_for_logged_in_user(request):
    if IsAdmin().has_permission(request, None):
        return redirect('dashboards:admin_dashboard')
    if IsDoctor().has_permission(request, None):
        return redirect('dashboards:doctor_dashboard')
    if IsReceptionist().has_permission(request, None):
        return redirect('dashboards:receptionist_dashboard')
    if IsPatient().has_permission(request, None):
        return redirect('appointment:patient_dashboard')
    return render(request, 'home.html')


def role_required(permission_class):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/login/')

            if not permission_class().has_permission(request, None):
                return _redirect_for_logged_in_user(request)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator