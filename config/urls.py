from django.contrib import admin
from django.urls import include, path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path(
        "api/auth/token/",
        TokenObtainPairView.as_view(),
        name="token-obtain-pair",
    ),
    path(
        "api/auth/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("api/", include("products.urls")),
    path("api/", include("cart.urls")),
    path("api/", include("orders.urls")),
]
