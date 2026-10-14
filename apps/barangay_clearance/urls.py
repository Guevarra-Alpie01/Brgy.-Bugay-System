from django.urls import path

from . import views

app_name = "barangay_clearance"
urlpatterns = [path("", views.create, name="create")]
