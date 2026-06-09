from rest_framework import serializers

from appointment.models import Appointment

ROLE_CHOICES = ['admin', 'doctor', 'patient', 'receptionist']


class ManagementUserSerializer(serializers.Serializer):
	id = serializers.IntegerField()
	name = serializers.CharField()
	initial = serializers.CharField()
	email = serializers.CharField()
	role = serializers.ChoiceField(choices=[(r, r) for r in ROLE_CHOICES])
	details = serializers.CharField()


class RoleUpdateSerializer(serializers.Serializer):
	role = serializers.ChoiceField(choices=[(r, r) for r in ROLE_CHOICES])


class ManagementAppointmentSerializer(serializers.ModelSerializer):
	patient_name = serializers.SerializerMethodField()
	doctor_name = serializers.SerializerMethodField()
	appointment_type = serializers.CharField(source='get_appointment_type_display')
	status = serializers.CharField(source='get_status_display')
	raw_status = serializers.CharField(source='status')
	appointment_code = serializers.SerializerMethodField()
	is_telemedicine = serializers.SerializerMethodField()

	class Meta:
		model = Appointment
		fields = [
			'id',
			'appointment_code',
			'patient_name',
			'doctor_name',
			'appointment_type',
			'date',
			'start_time',
			'end_time',
			'status',
			'raw_status',
			'is_telemedicine',
		]

	def get_patient_name(self, obj):
		return obj.patient.get_full_name() or obj.patient.username

	def get_doctor_name(self, obj):
		return obj.doctor.get_full_name() or obj.doctor.username

	def get_appointment_code(self, obj):
		return f"APT-{obj.id:03d}"

	def get_is_telemedicine(self, obj):
		return obj.appointment_type == 'telemedicine'
