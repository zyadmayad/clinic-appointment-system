from django.shortcuts import get_object_or_404, redirect, render
from auth.models import Users

def home(request):
    return render(request, "home.html")

def helloP(request):
    return render(request, "helloP.html")

def helloD(request):
    return render(request, "helloD.html")

def helloR(request):
    return render(request, "helloR.html")

def helloA(request):
    return render(request, "helloA.html")

def register(request):
    context = {}

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")

        if not full_name or not email or not phone or not password:
            context["error"] = "All fields are required."
        elif Users.objects.filter(email=email).exists():
            context["error"] = "This email is already registered."
        else:
            Users.objects.create(
                name=full_name,
                email=email,
                phone=phone,
                password=password,
                role="patient",
            )
            return redirect("auth:helloP")

    return render(request, "register.html", context)

def login(request):
    context = {}

    if request.method == "POST":
        email = request.POST.get("email") or request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = Users.objects.filter(email=email.strip(), password=password).first()
        if user and user.role == "admin":
            request.session["user_id"] = user.id
            request.session["user_name"] = user.name
            return redirect("auth:helloA")
        elif user and user.role == "doctor":
            request.session["user_id"] = user.id
            request.session["user_name"] = user.name
            return redirect("auth:helloD")
        elif user and user.role == "receptionist":
            request.session["user_id"] = user.id
            request.session["user_name"] = user.name
            return redirect("auth:helloR")
        elif user and user.role == "patient":
            request.session["user_id"] = user.id
            request.session["user_name"] = user.name
            return redirect("auth:helloP")

        context["error"] = "Invalid email or password."

    return render(request, "login.html", context)