from collections import defaultdict
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from appointment.models import Appointment
from auth.models import Users
from auth.permissions import IsAdmin
from managements.api.serializer import (
	ManagementAppointmentSerializer,
	ManagementUserSerializer,
	RoleUpdateSerializer,
)
from managements.views import list_users
from schedule.models import Schedule


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def users_list(request):
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

		user_items.append(
			{
				'id': account.id,
				'name': full_name,
				'initial': full_name[:1].upper(),
				'email': account.email or profile.email or '—',
				'role': profile.role,
				'details': details,
			}
		)

	serializer = ManagementUserSerializer(user_items, many=True)
	return Response(
		{
			'count': len(user_items),
			'search_query': search_query,
			'selected_role': selected_role,
			'results': serializer.data,
		}
	)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_role_update(request, user_id):
	serializer = RoleUpdateSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	selected_role = serializer.validated_data['role']

	profile = Users.objects.filter(user_id=user_id).first()
	if not profile:
		return Response({'detail': 'User profile not found.'}, status=status.HTTP_404_NOT_FOUND)

	if request.user.id == user_id and selected_role != 'admin':
		return Response(
			{'detail': 'You cannot remove your own admin role.'},
			status=status.HTTP_400_BAD_REQUEST,
		)

	profile.role = selected_role
	profile.save(update_fields=['role'])
	return Response({'detail': 'User role updated successfully.', 'role': selected_role})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def user_delete(request, user_id):
	if request.user.id == user_id:
		return Response(
			{'detail': 'You cannot delete your own account.'},
			status=status.HTTP_400_BAD_REQUEST,
		)

	account = User.objects.filter(id=user_id).first()
	if not account:
		return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

	account.delete()
	return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def appointments_list(request):
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

	serializer = ManagementAppointmentSerializer(appointments, many=True)
	return Response(
		{
			'count': len(serializer.data),
			'search_query': search_query,
			'selected_status': selected_status or 'all',
			'results': serializer.data,
		}
	)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdmin])
def doctor_schedules(request):
	doctors_qs = User.objects.filter(users__role='doctor').distinct().order_by('first_name', 'last_name', 'username')
	doctors = [
		{
			'id': doctor.id,
			'name': doctor.get_full_name() or doctor.username,
		}
		for doctor in doctors_qs
	]

	selected_doctor_id = request.GET.get('doctor', '').strip()
	selected_doctor = next((doctor for doctor in doctors if str(doctor['id']) == selected_doctor_id), None)
	if selected_doctor is None and doctors:
		selected_doctor = doctors[0]

	week_start_value = request.GET.get('week_start', '').strip()
	if week_start_value:
		try:
			week_start = date.fromisoformat(week_start_value)
		except ValueError:
			return Response({'detail': 'week_start must be YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
	else:
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

	today = timezone.localdate()
	weekly_schedule = []
	for day in week_days:
		day_records = schedule_by_date.get(day, [])
		shifts = []
		for record in day_records:
			if record.day_type == 'off':
				continue
			shifts.append({'time_range': f"{record.start_time.strftime('%H:%M')} - {record.end_time.strftime('%H:%M')}"})

		if not day_records:
			day_status = 'No schedule'
		elif any(record.day_type == 'off' for record in day_records):
			day_status = 'Day off'
		else:
			day_status = 'Working Day'

		weekly_schedule.append(
			{
				'name': day.strftime('%A'),
				'date': day.isoformat(),
				'status': day_status,
				'shifts': shifts,
				'is_today': day == today,
			}
		)

	return Response(
		{
			'doctors': doctors,
			'selected_doctor': selected_doctor,
			'week_start': week_start.isoformat(),
			'week_end': week_end.isoformat(),
			'weekly_schedule': weekly_schedule,
		}
	)
