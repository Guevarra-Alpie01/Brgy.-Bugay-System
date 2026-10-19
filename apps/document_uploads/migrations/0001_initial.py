import apps.document_uploads.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UploadedDocument",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("barangay-clearance", "Barangay Clearance"),
                            ("barangay-certificate", "Barangay Certificate"),
                            ("certificate-of-indigent", "Certificate of Indigent"),
                            ("certificate-of-agreement", "Certificate of Agreement"),
                            ("cattle-clearance", "Cattle Clearance"),
                            ("cutting-permit", "Cutting Permit"),
                            ("conference-letter", "Conference Letter"),
                        ],
                        max_length=40,
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to=apps.document_uploads.models.uploaded_file_path
                    ),
                ),
                ("original_name", models.CharField(max_length=255)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="document_uploads",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-uploaded_at",),
            },
        ),
    ]
