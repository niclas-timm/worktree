from django.urls import path

from .views import MyCompanyView

urlpatterns = [
    path("my/", MyCompanyView.as_view(), name="my-company"),
]
