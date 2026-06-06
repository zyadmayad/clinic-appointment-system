from slots.models import Slot

def book_slot(doctor_id, date, start_time, end_time):
    slot = Slot.objects.select_for_update().filter(
        doctor_id=doctor_id, date=date,
        start_time=start_time, end_time=end_time,
    ).first()

    if not slot:
        raise ValueError("Requested slot not found. Please pick a valid slot.")
    if slot.status != 'available':
        raise ValueError("This slot is already booked.")

    slot.status = 'booked'
    slot.save(update_fields=['status'])
    return slot


def release_slot(*, slot_id=None, doctor_id=None, date=None, start_time=None, end_time=None):
    """Mark a booked slot available again. Prefer slot_id when the appointment still points at a Slot row."""
    if slot_id is not None:
        Slot.objects.filter(pk=slot_id, status='booked').update(status='available')
        return
    if doctor_id is None or date is None or start_time is None or end_time is None:
        return
    Slot.objects.filter(
        doctor_id=doctor_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        status='booked',
    ).update(status='available')


def slot_kwargs(obj):
    """Extract slot-related fields from an appointment or validated data dict."""
    is_dict = isinstance(obj, dict)
    return {
        'doctor_id': obj['doctor'].id if is_dict else obj.doctor_id,
        'date':       obj['date'],
        'start_time': obj['start_time'],
        'end_time':   obj['end_time'],
    }
