from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, re_path

from backend.config.views import FrontendView


def health_check(request):
    return JsonResponse({'status': 'ok', 'message': 'Django API is working'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),
    # API routes will go here under 'api/' prefix
    # path('api/', include('backend.apps.api.urls')),

    # Catch-all: serve React frontend for client-side routing
    re_path(r'^(?!admin|api|static).*$', FrontendView.as_view(), name='frontend'),
]
