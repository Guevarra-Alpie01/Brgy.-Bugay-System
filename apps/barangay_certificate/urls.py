from django.urls import path

from . import views

app_name = "barangay_certificate"
urlpatterns = [path("", views.create, name="create")]
