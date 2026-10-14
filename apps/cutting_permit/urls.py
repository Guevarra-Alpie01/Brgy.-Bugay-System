from django.urls import path

from . import views

app_name = "cutting_permit"
urlpatterns = [path("", views.create, name="create")]
