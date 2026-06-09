from datetime import date, datetime, time

from django.utils.dateparse import parse_time

from slots.models import Slot


def coerce_time(value):
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        t = parse_time(value)
        if t is None:
            raise ValueError('Invalid time value.')
        return t
    raise ValueError('Time must be a string or time instance.')


def ranges_overlap_same_day(day: date, start_a, end_a, start_b, end_b) -> bool:
    if start_a >= end_a or start_b >= end_b:
        return False
    a1 = datetime.combine(day, start_a)
    b1 = datetime.combine(day, end_a)
    a2 = datetime.combine(day, start_b)
    b2 = datetime.combine(day, end_b)
    return a1 < b2 and a2 < b1

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
    is_dict = isinstance(obj, dict)
    return {
        'doctor_id': obj['doctor'].id if is_dict else obj.doctor_id,
        'date':       obj['date'],
        'start_time': obj['start_time'],
        'end_time':   obj['end_time'],
    }
