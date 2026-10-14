from django.urls import path

from . import views

app_name = "cattle_clearance"
urlpatterns = [path("", views.create, name="create")]
