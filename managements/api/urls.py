from django.urls import path

from managements.api import views


urlpatterns = [
	path('users/', views.users_list, name='users_list'),
	path('users/<int:user_id>/role/', views.user_role_update, name='user_role_update'),
	path('users/<int:user_id>/', views.user_delete, name='user_delete'),
	path('appointments/', views.appointments_list, name='appointments_list'),
	path('doctor-schedules/', views.doctor_schedules, name='doctor_schedules'),
]
