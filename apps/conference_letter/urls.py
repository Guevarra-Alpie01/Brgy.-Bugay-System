from django.urls import path

from . import views

app_name = "conference_letter"
urlpatterns = [path("", views.create, name="create")]
