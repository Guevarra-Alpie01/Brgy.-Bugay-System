from django.urls import path

from . import views


app_name = "document_uploads"

urlpatterns = [
    path("<slug:category>/", views.category_files, name="category"),
    path("file/<int:pk>/", views.view_file, name="file"),
]
