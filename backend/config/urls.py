from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path, re_path

from backend.config.views import FrontendView


def health_check(request):
    return JsonResponse({"status": "ok", "message": "Django API is working"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health_check"),
    # Authentication (custom endpoints first to override dj_rest_auth defaults)
    path("api/auth/", include("backend.apps.users.urls")),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    # Catch-all: serve React frontend for client-side routing
    re_path(r"^(?!admin|api|static).*$", FrontendView.as_view(), name="frontend"),
]
