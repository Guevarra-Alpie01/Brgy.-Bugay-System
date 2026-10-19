from django.urls import path

from . import views


app_name = "document_uploads"

urlpatterns = [
    path("<slug:category>/", views.category_files, name="category"),
    path("file/<int:pk>/", views.view_file, name="file"),
    path("file/<int:pk>/content/", views.document_content, name="content"),
    path("file/<int:pk>/callback/", views.editor_callback, name="callback"),
]
