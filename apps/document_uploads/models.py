import uuid
from pathlib import Path

from django.conf import settings
from django.db import models


DOCUMENT_CATEGORIES = (
    ("barangay-clearance", "Barangay Clearance"),
    ("barangay-certificate", "Barangay Certificate"),
    ("certificate-of-indigent", "Certificate of Indigent"),
    ("certificate-of-agreement", "Certificate of Agreement"),
    ("cattle-clearance", "Cattle Clearance"),
    ("cutting-permit", "Cutting Permit"),
    ("conference-letter", "Conference Letter"),
)


def uploaded_file_path(instance, filename):
    extension = Path(filename).suffix[:16]
    return f"document_uploads/{instance.category}/{uuid.uuid4().hex}{extension}"


class UploadedDocument(models.Model):
    category = models.CharField(max_length=40, choices=DOCUMENT_CATEGORIES)
    file = models.FileField(upload_to=uploaded_file_path)
    original_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="document_uploads",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-uploaded_at",)

    def __str__(self):
        return self.original_name
