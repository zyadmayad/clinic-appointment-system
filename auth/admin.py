from django.contrib import admin
from auth.models import Users

# Register your models here.
@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'email', 'role', 'created_at', 'updated_at')
	list_filter = ('role',)
	search_fields = ('name', 'email')