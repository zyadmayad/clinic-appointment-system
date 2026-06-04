from collections import defaultdict
from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from appointment.models import Appointment
from auth.models import Users
from auth.permissions import IsAdmin
from schedule.models import Schedule

# Create your views here.

def check_admin(request):
  if not IsAdmin().has_permission(request, None):
    if not request.user.is_authenticated:
      return redirect('auth:login'), None
    return redirect('home'), None

  profile = Users.objects.filter(user=request.user).only('role').first()
  return None, {
    'user_name': request.user.username,
    'user_role': profile.role if profile else 'admin',
  }

def admin_appointments(request):
  denied, admin_context = check_admin(request)
  if denied:
    return denied

  search_query = request.GET.get('q', '').strip()
  selected_status = request.GET.get('status', '').strip()

  appointments = Appointment.objects.select_related('patient', 'doctor').order_by('-date', 'start_time')

  if selected_status and selected_status != 'all':
    appointments = appointments.filter(status=selected_status)

  if search_query:
    query_filters = (
      Q(patient__username__icontains=search_query)
      | Q(patient__first_name__icontains=search_query)
      | Q(patient__last_name__icontains=search_query)
      | Q(doctor__username__icontains=search_query)
      | Q(doctor__first_name__icontains=search_query)
      | Q(doctor__last_name__icontains=search_query)
      | Q(appointment_type__icontains=search_query)
    )

    normalized_code = search_query.lower().replace('apt-', '').strip()
    if normalized_code.isdigit():
      query_filters |= Q(id=int(normalized_code))

    appointments = appointments.filter(query_filters)

  appointment_items = []
  for appointment in appointments:
    patient_name = appointment.patient.get_full_name() or appointment.patient.username
    appointment_items.append({
      'patient_name': patient_name,
      'patient_initial': patient_name[:1].upper(),
      'doctor_name': appointment.doctor.get_full_name() or appointment.doctor.username,
      'appointment_type': appointment.get_appointment_type_display(),
      'date': appointment.date.strftime('%Y-%m-%d'),
      'start_time': appointment.start_time.strftime('%H:%M'),
      'end_time': appointment.end_time.strftime('%H:%M'),
      'status': appointment.get_status_display(),
      'raw_status': appointment.status,
      'appointment_code': f"APT-{appointment.id:03d}",
      'is_telemedicine': appointment.appointment_type == 'telemedicine',
    })

  return render(
    request,
    'admin/appointments.html',
    {
      **admin_context,
      'appointments': appointment_items,
      'appointments_count': len(appointment_items),
      'search_query': search_query,
      'selected_status': selected_status or 'all',
      'status_options': Appointment.STATUS_CHOICES,
      'active_admin_page': 'appointments',
    },
  )


def doctor_schedule(request):
  denied, admin_context = check_admin(request)
  if denied:
    return denied

  doctors_qs = User.objects.filter(users__role='doctor').distinct().order_by('first_name', 'last_name', 'username')
  doctors = [
    {
      'id': doctor.id,
      'name': doctor.get_full_name() or doctor.username,
      'specialty': 'General Practice',
      'initial': (doctor.get_full_name() or doctor.username)[:1].upper(),
    }
    for doctor in doctors_qs
  ]

  selected_doctor_id = request.GET.get('doctor', '').strip()
  selected_doctor = next((doctor for doctor in doctors if str(doctor['id']) == selected_doctor_id), None)
  if selected_doctor is None and doctors:
    selected_doctor = doctors[0]

  today = timezone.localdate()
  week_start = today - timedelta(days=today.weekday())
  week_days = [week_start + timedelta(days=index) for index in range(7)]
  week_end = week_days[-1]

  schedule_records = Schedule.objects.none()
  if selected_doctor:
    schedule_records = Schedule.objects.filter(
      doctor_id=selected_doctor['id'],
      date__range=(week_start, week_end),
    ).order_by('date', 'start_time')

  schedule_by_date = defaultdict(list)
  for record in schedule_records:
    schedule_by_date[record.date].append(record)

  weekly_schedule = []
  for day in week_days:
    day_records = schedule_by_date.get(day, [])
    shifts = []
    for record in day_records:
      if record.day_type == 'off':
        continue
      shifts.append({
        'time_range': f"{record.start_time.strftime('%H:%M')} - {record.end_time.strftime('%H:%M')}",
      })

    if not day_records:
      day_status = 'No schedule'
    elif any(record.day_type == 'off' for record in day_records):
      day_status = 'Day off'
    else:
      day_status = 'Working Day'

    weekly_schedule.append({
      'name': day.strftime('%A'),
      'date': day.strftime('%b %d'),
      'status': day_status,
      'shifts': shifts,
      'is_today': day == today,
    })

  schedule_exceptions = []
  if selected_doctor:
    off_records = Schedule.objects.filter(
      doctor_id=selected_doctor['id'],
      day_type='off',
      date__gte=today,
    ).order_by('date')[:4]

    for record in off_records:
      schedule_exceptions.append({
        'date': record.date.strftime('%Y-%m-%d'),
        'title': 'Day off',
        'detail': 'Scheduled unavailable',
        'tone': 'danger',
      })

  if not schedule_exceptions:
    schedule_exceptions.append({
      'date': 'No upcoming exceptions',
      'title': 'All clear',
      'detail': 'No scheduled exceptions for the selected doctor.',
      'tone': 'neutral',
    })

  total_working_days = sum(1 for day in weekly_schedule if day['shifts'])
  total_shifts = sum(len(day['shifts']) for day in weekly_schedule)
  total_days_off = sum(1 for day in weekly_schedule if day['status'] == 'Day off')

  return render(
    request,
    'admin/doctor_schedules.html',
    {
      **admin_context,
      'doctors': doctors,
      'selected_doctor': selected_doctor,
      'week_range': f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}",
      'weekly_schedule': weekly_schedule,
      'schedule_exceptions': schedule_exceptions,
      'total_working_days': total_working_days,
      'total_shifts': total_shifts,
      'total_days_off': total_days_off,
      'active_admin_page': 'doctor_schedules',
    },
  )


def list_users(search_query="", selected_role="all"):
    users = Users.objects.select_related('user').filter(user__isnull=False).order_by('user__first_name', 'user__username')

    if selected_role and selected_role != 'all':
        users = users.filter(role=selected_role)

    if search_query:
        users = users.filter(
            Q(user__username__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(role__icontains=search_query)
        )

    return users


def user_managements(request):
  denied, admin_context = check_admin(request)
  if denied:
    return denied

  search_query = request.GET.get('q', '').strip()
  selected_role = request.GET.get('role', 'all').strip() or 'all'

  profiles = list_users(search_query=search_query, selected_role=selected_role)

  user_items = []
  for profile in profiles:
    account = profile.user
    full_name = account.get_full_name().strip() or profile.username or account.username

    details = '—'
    if profile.role == 'doctor':
      details = 'General Medicine'
    elif profile.role == 'patient':
      details = f"+1 555-{1000 + account.id}"

    user_items.append({
      'id': account.id,
      'name': full_name,
      'initial': full_name[:1].upper(),
      'email': account.email or profile.email or '—',
      'role': profile.role,
      'details': details,
    })

  return render(
    request,
    'admin/user_managements.html',
    {
      **admin_context,
      'users': user_items,
      'users_count': len(user_items),
      'search_query': search_query,
      'selected_role': selected_role,
      'active_admin_page': 'user_managements',
    },
  )


def update_user_role(request, user_id):
  denied, _ = check_admin(request)
  if denied:
    return denied

  if request.method != 'POST':
    return redirect('managements:user_managements')

  selected_role = (request.POST.get('role') or '').strip()
  valid_roles = {role for role, _ in Users.ROLE_CHOICES}
  if selected_role not in valid_roles:
    return redirect('managements:user_managements')

  profile = Users.objects.filter(user_id=user_id).first()
  if not profile:
    return redirect('managements:user_managements')

  # Keep at least one admin account accessible.
  if request.user.id == user_id and selected_role != 'admin':
    return redirect('managements:user_managements')

  profile.role = selected_role
  profile.save(update_fields=['role'])
  return redirect('managements:user_managements')


def delete_user(request, user_id):
  denied, _ = check_admin(request)
  if denied:
    return denied

  if request.method != 'POST':
    return redirect('managements:user_managements')

  # Prevent deleting the current logged-in admin.
  if request.user.id == user_id:
    return redirect('managements:user_managements')

  account = User.objects.filter(id=user_id).first()
  if account:
    account.delete()

  return redirect('managements:user_managements')