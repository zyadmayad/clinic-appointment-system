from django.contrib.auth.views import LoginView
from django.urls import path

from .views import home

app_name = 'auth'

urlpatterns = [
    path('', home, name='home'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('register/', LoginView.as_view(template_name='register.html'), name='register'),
]
