from django.urls import path
from .views import index, register, login_view, logout_view
from .views import index, register, login_view, logout_view, profile


urlpatterns = [
    path("", index, name="index"),
    path("register/", register, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile, name="profile"),
]