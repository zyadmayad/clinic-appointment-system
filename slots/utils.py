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


def release_slot(doctor_id, date, start_time, end_time):
    Slot.objects.filter(
        doctor_id=doctor_id, date=date,
        start_time=start_time, end_time=end_time,
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
