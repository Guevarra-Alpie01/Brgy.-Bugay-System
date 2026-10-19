from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import signing
from django.test import TestCase, override_settings
from django.urls import reverse
import jwt
from io import BytesIO
import json
from unittest.mock import patch
from tempfile import TemporaryDirectory

from apps.document_uploads.models import UploadedDocument


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
        self.account = get_user_model().objects.create_user(
            username="barangay-staff",
            password="test-password-123",
        )
        self.client.force_login(self.account)

    def test_home_lists_seven_separate_document_apps(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Create ")
        for category, label in DOCUMENTS:
            with self.subTest(document=label):
                self.assertContains(response, label)
                self.assertContains(
                    response,
                    reverse("document_uploads:category", args=[category]),
                )

    def test_landing_page_requires_login_and_login_page_hides_navigation(self):
        self.client.logout()
        response = self.client.get(reverse("home"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('home')}",
        )
        login_response = self.client.get(reverse("login"))
        self.assertEqual(login_response.status_code, 200)
        self.assertContains(login_response, 'name="username"')
        self.assertContains(login_response, 'name="password"')
        self.assertNotContains(login_response, "All documents")

    def test_successful_login_opens_document_navigation(self):
        self.client.logout()
        response = self.client.post(
            reverse("login"),
            {"username": "barangay-staff", "password": "test-password-123"},
        )

        self.assertRedirects(response, reverse("home"))
        home_response = self.client.get(reverse("home"))
        self.assertContains(home_response, "Barangay Document Services")
        self.assertContains(home_response, "Upload a file")
        self.assertContains(home_response, "Sign out")

    def test_sidebar_is_removed_and_upload_classifications_are_available(self):
        response = self.client.get(reverse("home"))

        self.assertNotContains(response, 'class="sidebar"')
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'name="category"')
        self.assertContains(response, reverse("document_uploads:category", args=["conference-letter"]))

    def test_upload_is_saved_and_accessible_under_its_classification(self):
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("home"),
                    {
                        "category": "barangay-clearance",
                        "file": SimpleUploadedFile(
                            "clearance.pdf",
                            b"Uploaded document contents",
                            content_type="application/pdf",
                        ),
                    },
                )

                self.assertRedirects(response, reverse("home"))
                home_response = self.client.get(reverse("home"))
                self.assertContains(home_response, "clearance.pdf")

                category_response = self.client.get(
                    reverse(
                        "document_uploads:category",
                        args=["barangay-clearance"],
                    )
                )
                self.assertContains(category_response, "clearance.pdf")

                document = category_response.context["documents"][0]
                file_response = self.client.get(
                    reverse("document_uploads:file", args=[document.pk])
                )
                self.assertEqual(file_response.status_code, 200)
                try:
                    self.assertEqual(
                        b"".join(file_response.streaming_content),
                        b"Uploaded document contents",
                    )
                finally:
                    file_response.close()
                self.assertEqual(
                    file_response["Content-Disposition"].split(";")[0],
                    "inline",
                )

    def test_upload_routes_require_login(self):
        self.client.logout()
        response = self.client.get(
            reverse(
                "document_uploads:category",
                args=["barangay-clearance"],
            )
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('document_uploads:category', args=['barangay-clearance'])}",
        )

    def test_failed_login_shows_error(self):
        self.client.logout()
        response = self.client.post(
            reverse("login"),
            {"username": "barangay-staff", "password": "wrong-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "username or password")

    def test_create_routes_are_removed(self):
        for category, label in DOCUMENTS:
            with self.subTest(document=label):
                response = self.client.get(f"/{category}/")
                self.assertEqual(response.status_code, 404)

    def test_office_document_opens_editor_without_download_permission(self):
        document = UploadedDocument.objects.create(
            category="barangay-clearance",
            file=SimpleUploadedFile("clearance.docx", b"office document"),
            original_name="clearance.docx",
            uploaded_by=self.account,
        )

        with override_settings(
            ONLYOFFICE_DOCUMENT_SERVER_URL="http://localhost:8080",
            ONLYOFFICE_BACKEND_URL="http://host.docker.internal:8000",
            ONLYOFFICE_JWT_SECRET="test-editor-secret-that-is-at-least-32-bytes",
        ):
            response = self.client.get(
                reverse("document_uploads:file", args=[document.pk])
            )

        self.assertEqual(response.status_code, 200)
        config = response.context["editor_config"]
        self.assertEqual(config["documentType"], "word")
        self.assertTrue(config["document"]["permissions"]["edit"])
        self.assertFalse(config["document"]["permissions"]["download"])
        self.assertTrue(config["document"]["permissions"]["print"])
        self.assertContains(response, "office_editor.js")

    def test_editor_callback_saves_changes_back_to_uploaded_file(self):
        secret = "test-editor-secret-that-is-at-least-32-bytes"
        document = UploadedDocument.objects.create(
            category="barangay-clearance",
            file=SimpleUploadedFile("clearance.docx", b"original document"),
            original_name="clearance.docx",
            uploaded_by=self.account,
        )
        callback_payload = {
            "key": f"{document.pk}-{document.revision}",
            "status": 2,
            "url": "http://localhost:8080/cache/edited.docx",
        }
        callback_token = signing.dumps(
            {"pk": document.pk},
            salt="document-uploads-callback",
        )
        auth_token = jwt.encode(callback_payload, secret, algorithm="HS256")
        callback_url = (
            reverse("document_uploads:callback", args=[document.pk])
            + f"?token={callback_token}"
        )

        with (
            override_settings(
                ONLYOFFICE_DOCUMENT_SERVER_URL="http://localhost:8080",
                ONLYOFFICE_JWT_SECRET=secret,
            ),
            patch(
                "apps.document_uploads.views.urlopen",
                return_value=BytesIO(b"edited document"),
            ),
            TemporaryDirectory() as media_root,
            override_settings(MEDIA_ROOT=media_root),
        ):
            response = self.client.post(
                callback_url,
                data=json.dumps(callback_payload),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {auth_token}",
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"error": 0})
            document.refresh_from_db()
            with document.file.open("rb") as edited_file:
                self.assertEqual(edited_file.read(), b"edited document")

        self.assertEqual(document.revision, 2)

    def test_editor_callback_rejects_invalid_jwt(self):
        document = UploadedDocument.objects.create(
            category="barangay-clearance",
            file=SimpleUploadedFile("clearance.docx", b"office document"),
            original_name="clearance.docx",
            uploaded_by=self.account,
        )
        callback_token = signing.dumps(
            {"pk": document.pk},
            salt="document-uploads-callback",
        )

        with override_settings(
            ONLYOFFICE_JWT_SECRET="test-editor-secret-that-is-at-least-32-bytes"
        ):
            response = self.client.post(
                reverse("document_uploads:callback", args=[document.pk])
                + f"?token={callback_token}",
                data=json.dumps({"key": f"{document.pk}-1", "status": 2}),
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 403)

    def test_unsupported_file_does_not_offer_a_download(self):
        document = UploadedDocument.objects.create(
            category="barangay-clearance",
            file=SimpleUploadedFile("archive.zip", b"archive"),
            original_name="archive.zip",
            uploaded_by=self.account,
        )

        response = self.client.get(
            reverse("document_uploads:file", args=[document.pk])
        )

        self.assertEqual(response.status_code, 415)
        self.assertIn(b"Downloading is disabled.", response.content)
        self.assertNotIn(document.file.url.encode(), response.content)
