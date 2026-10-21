from django.urls import path

from . import views


app_name = "document_uploads"

urlpatterns = [
    path(
        "file/<int:pk>/delete/",
        views.delete_uploaded_document,
        name="delete-upload",
    ),
    path("<slug:category>/", views.category_files, name="category"),
    path("file/<int:pk>/", views.view_file, name="file"),
    path("file/<int:pk>/preview/", views.preview_file, name="preview"),
]
