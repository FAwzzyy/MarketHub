from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, LoginForm
from django.contrib.auth.decorators import login_required


def index(request):
    return HttpResponse("Welcome to MarketHub")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            return HttpResponse("Account created successfully!")

    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {
        "form": form
    })


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(
                request,
                username=username,
                password=password
            )

            if user is not None:
                login(request, user)
                return HttpResponse("Login successful!")

            else:
                return HttpResponse("Invalid username or password")

    else:
        form = LoginForm()

    return render(request, "registration/login.html", {
        "form": form
    })


def logout_view(request):
    logout(request)
    return HttpResponse("Logout successful!")
@login_required
def profile(request):
    return render(request, "registration/profile.html", {
        "user": request.user
    })