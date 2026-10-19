from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render

from .models import DOCUMENT_CATEGORIES, UploadedDocument


@login_required
def category_files(request, category):
    category_names = dict(DOCUMENT_CATEGORIES)
    if category not in category_names:
        raise Http404("Document category not found.")

    documents = UploadedDocument.objects.filter(category=category)
    return render(
        request,
        "document_uploads/category_files.html",
        {
            "category": category,
            "category_name": category_names[category],
            "documents": documents,
        },
    )


@login_required
def view_file(request, pk):
    document = get_object_or_404(UploadedDocument, pk=pk)
    inline_types = {
        ".gif": "image/gif",
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    content_type = inline_types.get(
        document.file.name.rsplit(".", 1)[-1].lower()
        if "." in document.file.name
        else ""
    )
    response = FileResponse(
        document.file.open("rb"),
        as_attachment=content_type is None,
        filename=document.original_name,
        content_type=content_type or "application/octet-stream",
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response
