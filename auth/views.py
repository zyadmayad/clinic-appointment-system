from django.shortcuts import redirect, render
from django.contrib.auth import logout as django_logout, authenticate, login as django_login
from django.contrib.auth.models import User
from auth.models import Users

def home(request):
    return render(request, "home.html")


def register(request):
    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        password = (request.POST.get("password") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()

        if not full_name or not email or not password:
            return render(request, 'register.html', {"error": "All fields are required"})
        
        if User.objects.filter(username=email).exists():
            return render(request, 'register.html', {"error": "Email already exists"})

        user = User.objects.create_user(
            username=email,
            password=password,
            email=email,
            first_name=full_name,
            last_name="",
        )

        profile, _ = Users.objects.get_or_create(user=user, defaults={'role': 'patient'})
        profile.username = user.username
        profile.email = user.email
        profile.password = user.password
        profile.save(update_fields=['username', 'email', 'password'])
        
        return redirect('home')

    return render(request, 'register.html')

def login(request):
    if request.method == "POST":
        identifier = (request.POST.get("email") or "").strip()
        password = request.POST.get("password")

        if not identifier or not password:
            return render(request, 'login.html', {"error": "Invalid credentials"})

        by_email = User.objects.filter(email__iexact=identifier).first()
        auth_username = by_email.username if by_email else identifier
        user = authenticate(request, username=auth_username, password=password)

        if user:
            django_login(request, user)

            profile = Users.objects.filter(user=user).first()
            role = profile.role if profile else 'patient'

            request.session['user_id'] = user.id
            request.session['user_role'] = role
            request.session['user_name'] = user.first_name or user.username
            request.session['user_email'] = user.email

            if role == 'admin':
                return redirect('clinic_admin:admin_dashboard')
            return redirect('home')

        return render(request, 'login.html', {"error": "Invalid credentials"})

    return render(request, 'login.html')

def logout(request):
    django_logout(request)
    return redirect('auth:login')
