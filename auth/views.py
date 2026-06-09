from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect, render
from .utils import _redirect_for_logged_in_user




def home(request):
    if request.user.is_authenticated and request.user.groups.exists():
        return _redirect_for_logged_in_user(request)
    return render(request, "home.html")



def register(request):
    if request.user.is_authenticated:
        return _redirect_for_logged_in_user(request)

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()

        if not username or not email or not password:
            return render(request, 'register.html', {"error": "All fields are required"})

        if User.objects.filter(username__iexact=username).exists():
            return render(request, 'register.html', {"error": "Username already exists"})

        if User.objects.filter(email__iexact=email).exists():
            return render(request, 'register.html', {"error": "Email already exists"})

        user = User.objects.create_user(username=username, password=password, email=email)

        patient_group, _ = Group.objects.get_or_create(name='patient')
        user.groups.add(patient_group)

        return redirect('auth:login')

    return render(request, 'register.html')


def login(request):
    if request.user.is_authenticated:
        return _redirect_for_logged_in_user(request)

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password")

        if not username or not password:
            return render(request, 'login.html', {"error": "Invalid credentials"})

        user = authenticate(request, username=username, password=password)

        if user:
            django_login(request, user)

            role_group = user.groups.first()
            role = role_group.name if role_group else 'patient'

            request.session['user_id'] = user.id
            request.session['user_role'] = role
            request.session['user_name'] = user.username
            request.session['user_email'] = user.email

            return _redirect_for_logged_in_user(request)

        return render(request, 'login.html', {"error": "Invalid credentials"})

    return render(request, 'login.html')


def logout(request):
    django_logout(request)
    return redirect('auth:login')
