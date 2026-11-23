from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView
from store.views import (
    LoginView,
    RegisterView,
    LogoutView,
    UserProfileView,
    ChangePasswordView,
)

def api_root_view(request):
    return JsonResponse({
        "project": "Car Craft Backend API",
        "status": "operational",
        "version": "1.0.0",
        "endpoints": {
            "admin": "/admin/",
            "auth": {
                "login": "/api/auth/login/",
                "register": "/api/auth/register/",
                "logout": "/api/auth/logout/",
                "profile": "/api/auth/profile/",
                "change_password": "/api/auth/change-password/",
                "refresh_token": "/api/auth/token/refresh/",
            },
            "store_api": "/api/",
            "products": "/api/products/",
            "categories": "/api/categories/",
            "brands": "/api/brands/",
            "car_makes": "/api/car-makes/",
            "car_models": "/api/car-models/",
            "garage": "/api/garage/",
            "custom_builds": "/api/custom-builds/",
            "services": "/api/services/",
            "bookings": "/api/bookings/",
            "cart": "/api/cart/",
            "orders": "/api/orders/",
            "custom_quotes": "/api/custom-quotes/",
            "dashboard_stats": "/api/dashboard/stats/",
        }
    })

urlpatterns = [
    path("", api_root_view, name="api-root-index"),
    path("admin/", admin.site.urls),
    path("api/health/", api_root_view, name="api-health"),

    # Authentication Endpoints
    path("api/auth/login/", LoginView.as_view(), name="auth-login"),
    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("api/auth/profile/", UserProfileView.as_view(), name="auth-profile"),
    path("api/auth/change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),

    # Main Store & Car Craft APIs
    path("api/", include("store.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
