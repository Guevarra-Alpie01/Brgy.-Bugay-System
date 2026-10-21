from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import zipfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.document_uploads.models import UploadedDocument
from apps.document_uploads.services.office_documents import (
    create_new_document,
    delete_document,
    file_location,
    find_office_executable,
    launch_document,
    rename_document,
    save_as_document,
)


DOCUMENTS = (
    ("barangay-clearance", "Barangay Clearance"),
    ("barangay-certificate", "Barangay Certificate"),
    ("certificate-of-indigent", "Certificate of Indigent"),
    ("certificate-of-agreement", "Certificate of Agreement"),
    ("cattle-clearance", "Cattle Clearance"),
    ("cutting-permit", "Cutting Permit"),
    ("conference-letter", "Conference Letter"),
)


class DocumentAppTests(TestCase):
    def setUp(self):
        self.media_temp = TemporaryDirectory(prefix="Document app test ")
        self.addCleanup(self.media_temp.cleanup)
        self.media_override = override_settings(MEDIA_ROOT=self.media_temp.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.account = get_user_model().objects.create_user(
            username="barangay-staff",
            password="test-password-123",
        )
        self.client.force_login(self.account)

    def create_document(self, name, content=b"document contents", category="barangay-clearance"):
        return UploadedDocument.objects.create(
            category=category,
            file=SimpleUploadedFile(name, content),
            original_name=name,
            uploaded_by=self.account,
        )

    def test_home_lists_seven_separate_document_categories(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-panel-toggle="upload-form"')
        self.assertContains(response, 'data-panel-toggle="uploaded-files-panel"')
        self.assertContains(response, 'aria-expanded="false"')
        self.assertRegex(
            response.content.decode(),
            r'<form[^>]*id="upload-form"[^>]*hidden>',
        )
        self.assertContains(response, "<svg")
        self.assertContains(response, 'title="Upload a file"')
        self.assertNotContains(response, "Choose a document classification")
        self.assertContains(response, "/static/css/app.css")
        self.assertContains(response, "/static/js/app.js")
        self.assertNotContains(response, "https://")
        self.assertNotContains(response, "http://")
        self.assertContains(response, "Uploaded files")
        self.assertContains(response, "No uploaded files.")
        for category, label in DOCUMENTS:
            with self.subTest(document=label):
                self.assertContains(response, label)
                self.assertContains(
                    response,
                    reverse("document_uploads:category", args=[category]),
                )

    def test_classification_link_opens_newest_uploaded_file_directly(self):
        older_document = self.create_document(
            "older.docx",
            category="barangay-clearance",
        )
        newest_document = self.create_document(
            "newest.docx",
            category="barangay-clearance",
        )

        response = self.client.get(reverse("home"))

        self.assertRegex(
            response.content.decode(),
            rf'<a href="{reverse("document_uploads:file", args=[newest_document.pk])}">Barangay Clearance</a>',
        )
        self.assertNotRegex(
            response.content.decode(),
            rf'<a href="{reverse("document_uploads:file", args=[older_document.pk])}">Barangay Clearance</a>',
        )
        self.assertNotContains(response, "Manage files")

    @patch("apps.document_uploads.views.launch_document")
    def test_office_file_link_launches_document_and_returns_home(
        self,
        launch,
    ):
        document = self.create_document("latest.docx", category="barangay-clearance")

        response = self.client.get(
            reverse("document_uploads:file", args=[document.pk]),
        )

        self.assertRedirects(
            response,
            reverse("home"),
        )
        launch.assert_called_once()
        self.assertEqual(launch.call_args.args[0].pk, document.pk)

    @patch(
        "apps.document_uploads.views.launch_document",
        side_effect=RuntimeError("Microsoft Word is not installed."),
    )
    def test_failed_office_open_returns_home_with_helpful_message(
        self,
        _launch,
    ):
        document = self.create_document("latest.docx", category="barangay-clearance")

        response = self.client.get(
            reverse("document_uploads:file", args=[document.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Could not open latest.docx in Microsoft Word.")
        self.assertNotContains(response, "UploadedDocument matching query does not exist")

    def test_landing_page_and_login_navigation(self):
        self.client.logout()
        response = self.client.get(reverse("home"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")
        login_response = self.client.get(reverse("login"))
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, 'name="username"')
        self.assertContains(login_response, 'name="password"')
        self.assertNotContains(login_response, "All documents")

    def test_upload_form_expands_when_validation_errors_need_attention(self):
        response = self.client.post(reverse("home"), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-label="Hide upload form"')
        self.assertContains(response, 'aria-expanded="true"')
        self.assertRegex(
            response.content.decode(),
            r'<button[^>]*aria-label="Hide upload form"[^>]*aria-expanded="true"',
        )
        self.assertNotRegex(
            response.content.decode(),
            r'<form[^>]*id="upload-form"[^>]*hidden>',
        )

    def test_file_panel_groups_uploads_by_category_with_delete_actions(self):
        clearance = self.create_document("clearance.pdf", category="barangay-clearance")
        certificate = self.create_document(
            "certificate.docx",
            category="barangay-certificate",
        )

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Barangay Clearance")
        self.assertContains(response, "Barangay Certificate")
        self.assertContains(response, clearance.original_name)
        self.assertContains(response, certificate.original_name)
        self.assertContains(
            response,
            reverse("document_uploads:delete-upload", args=[clearance.pk]),
        )
        self.assertContains(response, 'aria-label="Delete clearance.pdf"')

    def test_delete_upload_requires_post_and_removes_the_file_and_record(self):
        document = self.create_document("remove-me.pdf")
        document_path = Path(document.file.path)
        referenced_document = self.create_document(
            "keep-me.docx",
            category="barangay-certificate",
        )
        referenced_path = Path(referenced_document.file.path)
        orphan_path = (
            Path(self.media_temp.name)
            / "document_uploads"
            / "barangay-clearance"
            / "orphaned.docx"
        )
        orphan_path.parent.mkdir(parents=True, exist_ok=True)
        orphan_path.write_bytes(b"orphaned file")

        get_response = self.client.get(
            reverse("document_uploads:delete-upload", args=[document.pk])
        )
        self.assertEqual(get_response.status_code, 405)

        response = self.client.post(
            reverse("document_uploads:delete-upload", args=[document.pk])
        )

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(document_path.exists())
        self.assertFalse(UploadedDocument.objects.filter(pk=document.pk).exists())
        self.assertFalse(orphan_path.exists())
        self.assertTrue(referenced_path.exists())

    def test_delete_upload_requires_login(self):
        document = self.create_document("private.pdf")
        self.client.logout()

        response = self.client.post(
            reverse("document_uploads:delete-upload", args=[document.pk])
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('document_uploads:delete-upload', args=[document.pk])}",
        )

    def test_successful_login_opens_document_navigation(self):
        self.client.logout()
        response = self.client.post(
            reverse("login"),
            {"username": "barangay-staff", "password": "test-password-123"},
        )

        self.assertRedirects(response, reverse("home"))
        self.assertContains(self.client.get(reverse("home")), "Barangay Document Services")

    def test_upload_is_saved_in_its_category_and_pdf_can_be_previewed(self):
        response = self.client.post(
            reverse("home"),
            {
                "category": "barangay-clearance",
                "file": SimpleUploadedFile(
                    "clearance.pdf",
                    b"%PDF-1.4 test document",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertRedirects(response, reverse("home"))
        document = UploadedDocument.objects.get(original_name="clearance.pdf")
        category_response = self.client.get(
            reverse("document_uploads:category", args=[document.category])
        )
        self.assertContains(category_response, "clearance.pdf")
        self.assertNotContains(category_response, "Save As")

        self.create_document("request.docx")
        category_response = self.client.get(
            reverse("document_uploads:category", args=[document.category])
        )
        self.assertContains(category_response, "request.docx")
        self.assertNotContains(category_response, "Save As")
        self.assertNotContains(category_response, "Rename")
        self.assertNotContains(category_response, "Print")

        detail_response = self.client.get(
            reverse("document_uploads:file", args=[document.pk])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "PDF editing is not provided")

        preview_response = self.client.get(
            reverse("document_uploads:preview", args=[document.pk])
        )
        try:
            self.assertEqual(preview_response.status_code, 200)
            self.assertEqual(preview_response["Content-Type"], "application/pdf")
            self.assertEqual(preview_response["Content-Disposition"], "inline")
        finally:
            preview_response.close()

    def test_upload_rejects_multiple_files_without_saving_any(self):
        response = self.client.post(
            reverse("home"),
            {
                "category": "barangay-clearance",
                "file": [
                    SimpleUploadedFile("first.pdf", b"first"),
                    SimpleUploadedFile("second.pdf", b"second"),
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Upload one file at a time.")
        self.assertEqual(UploadedDocument.objects.count(), 0)

    def test_upload_allows_one_file_per_category_and_rejects_another(self):
        for category, _name in DOCUMENTS:
            with self.subTest(category=category):
                response = self.client.post(
                    reverse("home"),
                    {
                        "category": category,
                        "file": SimpleUploadedFile(
                            f"{category}.pdf",
                            b"first document",
                        ),
                    },
                )
                self.assertRedirects(response, reverse("home"))

        self.assertEqual(UploadedDocument.objects.count(), len(DOCUMENTS))
        original = UploadedDocument.objects.get(category="barangay-clearance")
        original_path = Path(original.file.path)

        response = self.client.post(
            reverse("home"),
            {
                "category": "barangay-clearance",
                "file": SimpleUploadedFile("second.pdf", b"second document"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "This classification already has a file. Delete it before uploading another.",
        )
        self.assertEqual(
            UploadedDocument.objects.filter(category="barangay-clearance").count(),
            1,
        )
        self.assertTrue(original_path.exists())
        self.assertFalse(
            any(
                Path(document.file.path).name == "second.pdf"
                for document in UploadedDocument.objects.all()
            )
        )

    @patch("apps.document_uploads.views.launch_document")
    def test_word_and_excel_file_links_launch_the_associated_office_app(
        self,
        launch,
    ):
        for name, office_kind in (("request.docx", "Word"), ("ledger.xlsx", "Excel")):
            with self.subTest(name=name):
                document = self.create_document(name)
                response = self.client.get(
                    reverse("document_uploads:file", args=[document.pk]),
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f"Opened {name} in Microsoft {office_kind}.")
        self.assertEqual(launch.call_count, 2)

    def test_category_must_be_valid(self):
        response = self.client.get(
            reverse("document_uploads:category", args=["not-a-category"])
        )
        self.assertEqual(response.status_code, 404)

    def test_document_routes_require_login(self):
        document = self.create_document("request.docx")
        self.client.logout()

        response = self.client.get(
            reverse("document_uploads:file", args=[document.pk])
        )
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('document_uploads:file', args=[document.pk])}",
        )

    def test_unsupported_file_is_not_previewed(self):
        document = self.create_document("archive.zip")
        response = self.client.get(
            reverse("document_uploads:file", args=[document.pk])
        )

        self.assertEqual(response.status_code, 415)
        self.assertContains(response, "Downloading is disabled.", status_code=415)


class OfficeDocumentServiceTests(TestCase):
    def setUp(self):
        self.media_temp = TemporaryDirectory(prefix="Bugay files ")
        self.addCleanup(self.media_temp.cleanup)
        self.media_root = Path(self.media_temp.name)
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.account = get_user_model().objects.create_user(
            username="office-user",
            password="test-password-123",
        )

    def make_document(self, name, content=b"original bytes"):
        return UploadedDocument.objects.create(
            category="barangay-clearance",
            file=SimpleUploadedFile(name, content),
            original_name=name,
            uploaded_by=self.account,
        )

    def category_folder(self):
        folder = self.media_root / "document_uploads" / "barangay-clearance"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    @patch("apps.document_uploads.services.office_documents.find_office_executable")
    @patch("apps.document_uploads.services.office_documents.subprocess.Popen")
    def test_launch_uses_argument_list_and_supports_unicode_paths(
        self,
        popen,
        find_executable,
    ):
        document = self.make_document("Résumé budget.xlsx")
        find_executable.return_value = Path(
            "C:/Program Files/Microsoft Office/EXCEL.EXE"
        )

        message = launch_document(document)

        self.assertIn("Résumé budget.xlsx", message)
        args, kwargs = popen.call_args
        self.assertEqual(args[0][0], str(find_executable.return_value))
        self.assertEqual(args[0][1], str(file_location(document)))
        self.assertIs(kwargs["shell"], False)

    def test_file_location_rejects_paths_outside_media_root(self):
        outside_path = self.media_root.parent / "outside.docx"
        outside_path.write_bytes(b"outside")
        self.addCleanup(lambda: outside_path.unlink(missing_ok=True))
        document = self.make_document("inside.docx")
        document.file.name = f"../{outside_path.name}"

        with self.assertRaises(ValidationError):
            file_location(document)

    @patch("apps.document_uploads.services.office_documents.shutil.which", return_value=None)
    @patch(
        "apps.document_uploads.services.office_documents._registry_office_paths",
        return_value=[],
    )
    def test_missing_office_application_has_clear_error(self, _registry, _which):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Microsoft Word is not installed"):
                find_office_executable("word")

    @patch("apps.document_uploads.services.office_documents.launch_document")
    @patch("apps.document_uploads.services.office_documents.find_office_executable")
    def test_create_new_word_document_is_valid_openxml_and_launches(
        self,
        find_executable,
        launch,
    ):
        find_executable.return_value = Path("WINWORD.EXE")
        destination = self.category_folder() / "New certificate.docx"

        result = create_new_document(
            "barangay-clearance",
            "word",
            ask_save_path=lambda category, extension: destination,
        )

        document = UploadedDocument.objects.get(original_name=destination.name)
        self.assertTrue(zipfile.is_zipfile(destination))
        self.assertEqual(file_location(document), destination.resolve())
        self.assertIn(destination.name, result)
        launch.assert_called_once_with(document)

    def test_create_new_document_rejects_existing_filename(self):
        folder = self.category_folder()
        destination = folder / "Already there.docx"
        destination.write_bytes(b"existing")

        with self.assertRaises(FileExistsError):
            create_new_document(
                "barangay-clearance",
                "word",
                ask_save_path=lambda category, extension: destination,
                launch=False,
            )
        self.assertEqual(destination.read_bytes(), b"existing")

    @patch("apps.document_uploads.services.office_documents.launch_document")
    def test_save_as_makes_separate_copy_and_keeps_original(self, launch):
        source = self.make_document("source.docx", b"original office bytes")
        destination = self.category_folder() / "Copy with spaces.docx"

        result = save_as_document(
            source,
            ask_save_path=lambda category, extension, name: destination,
        )

        copied = UploadedDocument.objects.get(original_name=destination.name)
        self.assertEqual(file_location(source).read_bytes(), b"original office bytes")
        self.assertEqual(file_location(copied).read_bytes(), b"original office bytes")
        self.assertIn("separate copy", result)
        launch.assert_called_once_with(copied)

    def test_rename_changes_file_and_display_name(self):
        document = self.make_document("before.docx")
        old_path = file_location(document)

        rename_document(document, "New name.docx")

        document.refresh_from_db()
        self.assertEqual(document.original_name, "New name.docx")
        self.assertFalse(old_path.exists())
        self.assertTrue(file_location(document).is_file())

    def test_rename_rejects_path_input_and_extension_change(self):
        document = self.make_document("before.docx")

        with self.assertRaises(ValidationError):
            rename_document(document, "..\\outside.docx")
        with self.assertRaises(ValidationError):
            rename_document(document, "changed.xlsx")
        self.assertEqual(document.original_name, "before.docx")

    def test_delete_removes_database_record_and_file(self):
        document = self.make_document("remove.docx")
        path = file_location(document)

        delete_document(document)

        self.assertFalse(path.exists())
        self.assertFalse(UploadedDocument.objects.filter(pk=document.pk).exists())
