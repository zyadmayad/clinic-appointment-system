from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.shortcuts import redirect, render

from appointment.models import Appointment
from schedule.models import Schedule


def patient_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('auth:login')

    user_name = request.user.get_full_name() or request.user.username
    today = datetime.now().date()

    appointments = Appointment.objects.filter(patient=request.user).select_related('doctor')

    upcoming = appointments.filter(date__gte=today).exclude(status='cancelled').count()
    today_apts = appointments.filter(date=today).exclude(status='cancelled')
    completed = appointments.filter(status='completed').count()
    pending = appointments.filter(status='requested').count()

    return render(request, 'patient/patient_dashboard.html', {
        'user_name': user_name,
        'today': today,
        'upcoming_count': upcoming,
        'today_count': today_apts.count(),
        'completed_count': completed,
        'pending_count': pending,
        'today_appointments': today_apts.order_by('start_time'),
    })


def book_appointment(request):
    if not request.user.is_authenticated:
        return redirect('auth:login')

    user_name = request.user.get_full_name() or request.user.username

    doctor_ids = Schedule.objects.filter(day_type='working').values_list('doctor_id', flat=True).distinct()
    doctors = User.objects.filter(id__in=doctor_ids)

    return render(request, 'patient/book_appointment.html', {
        'user_name': user_name,
        'doctors': doctors,
    })


def my_appointments(request):
    if not request.user.is_authenticated:
        return redirect('auth:login')

    user_name = request.user.get_full_name() or request.user.username

    appointments = (
        Appointment.objects
        .filter(patient=request.user)
        .select_related('doctor')
        .order_by('-date', '-start_time')
    )

    return render(request, 'patient/my_appointments.html', {
        'user_name': user_name,
        'appointments': appointments,
    })
