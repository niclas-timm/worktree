from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.generic import TemplateView


class FrontendView(TemplateView):
    """Serve the React frontend index.html for client-side routing."""

    template_name = 'index.html'

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # In development, this view won't be used (React runs on port 3000)
        # In production, serve the built React app
        if settings.DEBUG and not (settings.FRONTEND_DIR / 'index.html').exists():
            return HttpResponse(
                'Frontend not built. Run npm build in the frontend directory.',
                status=501,
            )
        return super().get(request, *args, **kwargs)
