from django.urls import path

from auth.api.views import current_user_detail, user_detail, user_list

urlpatterns = [
	path('users/', user_list, name='users_api_list'),
	path('user/account/', current_user_detail, name='users_api_account'),
	path('users/<int:user_id>/', user_detail, name='users_api_detail'),
]