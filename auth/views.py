from django.shortcuts import redirect, render
from django.contrib.auth import logout as django_logout, authenticate, login as django_login
from django.contrib.auth.models import User
from auth.models import Users
from auth.permissions import IsAdmin, IsDoctor, IsPatient, IsReceptionist


def home(request):
    return render(request, "home.html")

def register(request):
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

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
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
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password")

        if not username or not password:
            return render(request, 'login.html', {"error": "Invalid credentials"})

        user = authenticate(request, username=username, password=password)

        if user:
            django_login(request, user)

            profile = Users.objects.filter(user=user).first()
            role = profile.role if profile else 'patient'

            request.session['user_id'] = user.id
            request.session['user_role'] = role
            request.session['user_name'] = user.first_name or user.username
            request.session['user_email'] = user.email

            if IsAdmin().has_permission(request, None):
                return redirect('dashboards:admin_dashboard')
            
            if IsDoctor().has_permission(request, None):
                return redirect('dashboards:doctor_dashboard')
            
            if IsReceptionist().has_permission(request, None):
                return redirect('dashboards:receptionist_dashboard')
            
            if IsPatient().has_permission(request, None):
                return redirect('dashboards:patient_dashboard')
            
            return redirect('home')
            return redirect('appointment:patient_dashboard')
       

        return render(request, 'login.html', {"error": "Invalid credentials"})

    return render(request, 'login.html')

def logout(request):
    django_logout(request)
    return redirect('auth:login')
