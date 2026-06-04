from django.shortcuts import get_object_or_404, redirect, render

from appointment.models import Appointment
from auth.permissions import IsDoctor, IsPatient

from .models import Consultation


def _require_doctor(request):
    if IsDoctor().has_permission(request, None):
        return None
    if not request.user.is_authenticated:
        return redirect('auth:login')
    return redirect('home')


def _split_items(value):
    if not value:
        return []

    return [
        line.strip()
        for line in value.replace(',', '\n').splitlines()
        if line.strip()
    ]


def index(request):
    permission_result = _require_doctor(request)
    if permission_result:
        return permission_result

    appointments = Appointment.objects.filter(
        doctor=request.user,
    ).select_related('patient',
    ).order_by(
        '-date',
        '-start_time',
    )

    appointment_ids = list(appointments.values_list('id', flat=True))
    consultation_qs = Consultation.objects.filter(
        doctor=request.user,appointment_id__in=appointment_ids,).order_by('-updated_at','-id',)

    consultation_by_appointment = {}
    for consultation in consultation_qs:
        consultation_by_appointment.setdefault(consultation.appointment_id, consultation)

    appointment_items = []
    for appointment in appointments:
        patient_name = appointment.patient.username
        appointment_items.append({
            'appointment': appointment,
            'patient_name': patient_name,
            'patient_initial': patient_name[:1].upper(),
            'consultation': consultation_by_appointment.get(appointment.id),
        })

    return render(request, 'doctor/consultation.html', {
        'user_name': request.user.username,
        'appointment_items': appointment_items,
    })


def fill(request, appointment_id):
    permission_result = _require_doctor(request)
    if permission_result:
        return permission_result

    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor', 'patient'),
        id=appointment_id,
        doctor=request.user,
    )

    if appointment.status != 'checked_in':
        return redirect('consultations:index')

    consultation = Consultation.objects.filter(doctor=request.user,appointment=appointment,
    ).order_by('-updated_at','-id',).first()

    if consultation is None:
        consultation = Consultation(
            doctor=request.user,
            patient=appointment.patient,
            appointment=appointment,
        )

    error_message = ''
    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis').strip()
        notes = request.POST.get('notes').strip()
        prescriptions = request.POST.get('prescriptions').strip()
        tests = request.POST.get('tests').strip()

        if not diagnosis:
            error_message = 'Diagnosis is required.'
        else:
            consultation.doctor = request.user
            consultation.patient = appointment.patient
            consultation.appointment = appointment
            consultation.diagnosis = diagnosis
            consultation.notes = notes
            consultation.prescriptions = prescriptions
            consultation.tests = tests
            consultation.save()

            if appointment.status != 'completed':
                appointment.status = 'completed'
                appointment.save(update_fields=['status'])

            return redirect('consultations:summary', appointment_id=appointment.id)

    return render(request, 'doctor/consultation_form.html', {
        'user_name': request.user.username,
        'appointment': appointment,
        'consultation': consultation,
        'error_message': error_message,
    })


def summary(request, appointment_id):
    if not request.user.is_authenticated:
        return redirect('auth:login')

    is_doctor = IsDoctor().has_permission(request, None)
    is_patient = IsPatient().has_permission(request, None)

    if not is_doctor and not is_patient:
        return redirect('home')

    appointment_filters = {'id': appointment_id}
    if is_doctor:
        appointment_filters['doctor'] = request.user
    else:
        appointment_filters['patient'] = request.user
        appointment_filters['status'] = 'completed'

    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor', 'patient'),
        **appointment_filters,
    )

    consultation = Consultation.objects.filter(appointment=appointment).order_by(
        '-updated_at',
        '-id'
    ).first()

    if consultation is None:
        if is_doctor:
            return redirect('consultations:fill', appointment_id=appointment.id)
        return redirect('appointment:my_appointments')

    return render(request, 'doctor/consultation_summary.html', {
        'user_name': request.user.get_full_name() or request.user.username,
        'appointment': appointment,
        'consultation': consultation,
        'prescription_items': _split_items(consultation.prescriptions),
        'test_items': _split_items(consultation.tests),
        'is_patient': is_patient,
    })