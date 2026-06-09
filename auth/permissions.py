from rest_framework.permissions import BasePermission


def _has_role(user, role):
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=role).exists()


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, 'admin')


class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, 'doctor')


class IsReceptionist(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, 'receptionist')


class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return _has_role(request.user, 'patient')