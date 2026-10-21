import logging
from datetime import datetime, timezone as datetime_timezone
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import DOCUMENT_CATEGORIES, UploadedDocument
from .services.office_documents import (
    OFFICE_FILE_TYPES,
    cleanup_orphaned_document_files,
    delete_document,
    file_location,
    launch_document,
)

logger = logging.getLogger(__name__)

INLINE_TYPES = {
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".webp": "image/webp",
}


@login_required
def category_files(request, category):
    category_names = dict(DOCUMENT_CATEGORIES)
    if category not in category_names:
        raise Http404("Document category not found.")

    documents = UploadedDocument.objects.filter(category=category)
    document_rows = []
    for document in documents:
        try:
            location = file_location(document)
            modified_at = location.stat().st_mtime
        except (OSError, ValidationError):
            logger.exception("Could not read metadata for document %s.", document.pk)
            location = None
            modified_at = None
        extension = Path(document.original_name).suffix.lower()
        document_rows.append(
            {
                "document": document,
                "file_type": extension.lstrip(".").upper() or "Unknown",
                "location": str(location) if location else "File unavailable",
                "modified_at": (
                    timezone.localtime(
                        datetime.fromtimestamp(
                            modified_at,
                            tz=datetime_timezone.utc,
                        )
                    )
                    if modified_at is not None
                    else None
                ),
                "is_office_file": extension in OFFICE_FILE_TYPES,
            }
        )

    return render(
        request,
        "document_uploads/category_files.html",
        {
            "category": category,
            "category_name": category_names[category],
            "document_rows": document_rows,
        },
    )


@login_required
def view_file(request, pk):
    document = get_object_or_404(UploadedDocument, pk=pk)
    extension = Path(document.original_name).suffix.lower()
    if extension in OFFICE_FILE_TYPES:
        try:
            launch_document(document)
        except (OSError, RuntimeError, ValidationError) as error:
            logger.error(
                "Could not open document %s from its file link: %s",
                pk,
                error,
            )
            messages.error(
                request,
                f"Could not open {document.original_name} in Microsoft "
                f"{OFFICE_FILE_TYPES[extension].title()}. Check that Office "
                "is installed and the file is available.",
            )
        else:
            messages.success(
                request,
                f"Opened {document.original_name} in Microsoft "
                f"{OFFICE_FILE_TYPES[extension].title()}.",
            )
        return redirect("home")

    content_type = INLINE_TYPES.get(extension)
    if content_type is None:
        return render(
            request,
            "document_uploads/unsupported_file.html",
            {"document": document},
            status=415,
        )

    return render(
        request,
        "document_uploads/file_preview.html",
        {
            "document": document,
            "preview_url": reverse("document_uploads:preview", args=[document.pk]),
            "is_pdf": extension == ".pdf",
        },
    )


@login_required
def preview_file(request, pk):
    document = get_object_or_404(UploadedDocument, pk=pk)
    extension = Path(document.original_name).suffix.lower()
    content_type = INLINE_TYPES.get(extension)
    if not content_type:
        raise Http404("Preview is not available for this file.")
    try:
        response = FileResponse(
            document.file.open("rb"),
            as_attachment=False,
            filename=document.original_name,
            content_type=content_type,
        )
    except OSError:
        logger.exception("Could not open document %s for preview.", document.pk)
        raise Http404("Document file is unavailable.")
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = "inline"
    return response


@login_required
@require_POST
def delete_uploaded_document(request, pk):
    document = get_object_or_404(UploadedDocument, pk=pk)
    original_name = document.original_name
    try:
        delete_document(document)
    except (OSError, ValidationError):
        logger.exception("Could not delete document %s.", document.pk)
        messages.error(
            request,
            f"Could not delete {original_name}. The file may be unavailable or in use.",
        )
    else:
        messages.success(request, f"Deleted {original_name}.")
        try:
            cleanup_orphaned_document_files()
        except (OSError, ValidationError):
            logger.exception("Could not clean up orphaned document files.")
            messages.warning(
                request,
                "The selected file was deleted, but some unreferenced files "
                "could not be cleaned up.",
            )
    return redirect("home")
