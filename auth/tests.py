from types import SimpleNamespace

from django.contrib.auth.models import Group, User
from django.test import TestCase

from auth.permissions import IsAdmin, IsDoctor, IsPatient, IsReceptionist, _has_role


class RolePermissionTests(TestCase):
    def setUp(self):
        admin_group, _ = Group.objects.get_or_create(name='admin')
        doctor_group, _ = Group.objects.get_or_create(name='doctor')
        patient_group, _ = Group.objects.get_or_create(name='patient')

        self.admin = User.objects.create_user(username='admin_user')
        self.doctor = User.objects.create_user(username='doctor_user')
        self.patient = User.objects.create_user(username='patient_user')

        self.admin.groups.add(admin_group)
        self.doctor.groups.add(doctor_group)
        self.patient.groups.add(patient_group)

    def test_has_role_returns_true_for_matching_role(self):
        self.assertTrue(_has_role(self.doctor, 'doctor'))

    def test_has_role_returns_false_for_anonymous_user(self):
        from django.contrib.auth.models import AnonymousUser
        self.assertFalse(_has_role(AnonymousUser(), 'doctor'))

    def test_has_role_returns_false_for_mismatched_role(self):
        self.assertFalse(_has_role(self.patient, 'doctor'))

    def test_permission_classes_apply_expected_role_checks(self):
        admin_request = SimpleNamespace(user=self.admin)
        doctor_request = SimpleNamespace(user=self.doctor)
        patient_request = SimpleNamespace(user=self.patient)

        self.assertTrue(IsAdmin().has_permission(admin_request, None))
        self.assertTrue(IsDoctor().has_permission(doctor_request, None))
        self.assertTrue(IsPatient().has_permission(patient_request, None))

        self.assertFalse(IsReceptionist().has_permission(doctor_request, None))
        self.assertFalse(IsDoctor().has_permission(patient_request, None))
