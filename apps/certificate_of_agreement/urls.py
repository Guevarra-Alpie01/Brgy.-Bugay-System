from django.urls import path

from . import views

app_name = "certificate_of_agreement"
urlpatterns = [path("", views.create, name="create")]
