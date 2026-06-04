from django.contrib import admin
from auth.models import Users

# Register your models here.
@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'role')
	list_filter = ('role',)
	search_fields = ('user__username', 'user__email')