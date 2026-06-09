from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Unregister the default registration so we can add our customisation.
admin.site.unregister(User)

ROLE_NAMES = ['admin', 'doctor', 'patient', 'receptionist']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + ('get_role',)
    list_filter = BaseUserAdmin.list_filter + ('groups__name',)

    @admin.display(description='Role')
    def get_role(self, obj):
        group = obj.groups.filter(name__in=ROLE_NAMES).first()
        return group.name if group else '—'
