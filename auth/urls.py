from django.urls import path

from .views import home, login, register, helloA, helloD, helloR, helloP

app_name = 'auth'

urlpatterns = [
    path('', home, name='home'),
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('admen/', helloA, name='helloA'),
    path('doctor/', helloD, name='helloD'),
    path('receptionist/', helloR, name='helloR'),
    path('patient/', helloP, name='helloP')

]
