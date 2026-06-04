from django.urls import path

from .views import home, login, logout, register

app_name = 'auth'

urlpatterns = [
    path('', home, name='home'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),
]
