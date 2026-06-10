from django.shortcuts import get_object_or_404, redirect, render

from appointment.models import Appointment
from auth.permissions import IsDoctor, IsPatient, IsReceptionist
from auth.utils import role_required
from consultations.forms.consultationform import ConsultationForm

from .models import Consultation



def _split_items(value):
    if not value:
        return []

    return [
        line.strip()
        for line in value.replace(',', '\n').splitlines()
        if line.strip()
    ]

@role_required(IsDoctor)
def index(request):
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

@role_required(IsDoctor)
def fill(request, appointment_id):
    appointment = get_object_or_404(
        Appointment.objects.select_related("doctor", "patient"),
        id=appointment_id,
        doctor=request.user,
    )

    consultation = Consultation.objects.filter(
        doctor=request.user,
        appointment=appointment,
    ).order_by("-updated_at", "-id").first()

    if appointment.status != "checked_in" and consultation is None:
        return redirect("consultations:index")

    if consultation is None:
        consultation = Consultation(
            doctor=request.user,
            patient=appointment.patient,
            appointment=appointment,
        )

    if request.method == "POST":
        form = ConsultationForm(request.POST, instance=consultation)
        if form.is_valid():
            saved = form.save(commit=False)
            saved.doctor = request.user
            saved.patient = appointment.patient
            saved.appointment = appointment
            saved.save()

            if appointment.status != "completed":
                appointment.status = "completed"
                appointment.save(update_fields=["status"])

            return redirect("consultations:summary", appointment_id=appointment.id)
    else:
        form = ConsultationForm(instance=consultation)

    return render(
        request,
        "doctor/consultation_form.html",
        {
            "user_name": request.user.username,
            "appointment": appointment,
            "consultation": consultation,
            "form": form,
        },
    )

def _summary_for_role(request, appointment_id, role):
    is_doctor = IsDoctor().has_permission(request, None)
    is_patient = IsPatient().has_permission(request, None)
    is_receptionist = IsReceptionist().has_permission(request, None)

    if not is_doctor and not is_patient and not is_receptionist:
        return redirect('home')

    appointment_filters = {'id': appointment_id}
    if is_doctor:
        appointment_filters['doctor'] = request.user
    elif is_patient:
        appointment_filters['patient'] = request.user
        appointment_filters['status'] = 'completed'
    else:
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
        if is_receptionist:
            return redirect('receptionist:appointments_list')
        return redirect('appointment:my_appointments')

    return render(request, 'doctor/consultation_summary.html', {
        'user_name': request.user.get_full_name() or request.user.username,
        'appointment': appointment,
        'consultation': consultation,
        'prescription_items': _split_items(consultation.prescriptions),
        'test_items': _split_items(consultation.tests),
        'is_patient': is_patient,
        'is_receptionist': is_receptionist,
        'can_view_notes': is_doctor,
        'can_edit_consultation': is_doctor,
    })


@role_required(IsDoctor)
def doctor_summary(request, appointment_id):
    return _summary_for_role(request, appointment_id, role='doctor')

@role_required(IsReceptionist)
def receptionist_summary(request, appointment_id):
    return _summary_for_role(request, appointment_id, role='receptionist')

@role_required(IsPatient)
def patient_summary(request, appointment_id):
    return _summary_for_role(request, appointment_id, role='patient')