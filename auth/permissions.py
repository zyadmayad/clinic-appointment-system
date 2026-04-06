from rest_framework.permissions import BasePermission

from auth.models import Users

def _has_role(user, role):
    if not user or not user.is_authenticated:
        return False
    profile = Users.objects.filter(user=user).only('role').first()
    return bool(profile and profile.role == role)

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