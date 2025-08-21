from django.urls import path
from executor.views import run_code

urlpatterns = [
    path("run/", run_code,name="run_code"),
]
