from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from tempfile import TemporaryDirectory


DOCUMENTS = (
    ("barangay_clearance", "Barangay Clearance"),
    ("barangay_certificate", "Barangay Certificate"),
    ("certificate_of_indigent", "Certificate of Indigent"),
    ("certificate_of_agreement", "Certificate of Agreement"),
    ("cattle_clearance", "Cattle Clearance"),
    ("cutting_permit", "Cutting Permit"),
    ("conference_letter", "Conference Letter"),
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
        for app_name, label in DOCUMENTS:
            with self.subTest(document=label):
                self.assertContains(response, label)
                self.assertContains(response, reverse(f"{app_name}:create"))

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
                            "clearance.txt",
                            b"Uploaded document contents",
                            content_type="text/plain",
                        ),
                    },
                )

                self.assertRedirects(response, reverse("home"))
                home_response = self.client.get(reverse("home"))
                self.assertContains(home_response, "clearance.txt")

                category_response = self.client.get(
                    reverse(
                        "document_uploads:category",
                        args=["barangay-clearance"],
                    )
                )
                self.assertContains(category_response, "clearance.txt")

                document = category_response.context["documents"][0]
                file_response = self.client.get(
                    reverse("document_uploads:file", args=[document.pk])
                )
                self.assertEqual(
                    b"".join(file_response.streaming_content),
                    b"Uploaded document contents",
                )
                self.assertEqual(
                    file_response["Content-Disposition"].split(";")[0],
                    "attachment",
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

    def test_document_routes_require_login(self):
        self.client.logout()
        response = self.client.get(reverse("barangay_clearance:create"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('barangay_clearance:create')}",
        )

    def test_each_document_app_has_its_own_form_and_print_template(self):
        post_data = {
            "barangay_clearance": {
                "full_name": "Juan Dela Cruz",
                "address": "Barangay Sample",
                "purpose": "Employment",
                "years_of_residency": "10 years",
                "date_issued": "2026-10-13",
            },
            "barangay_certificate": {
                "full_name": "Juan Dela Cruz",
                "address": "Barangay Sample",
                "certified_information": "Resident of this barangay",
                "purpose": "School",
                "date_issued": "2026-10-13",
            },
            "certificate_of_indigent": {
                "full_name": "Juan Dela Cruz",
                "address": "Barangay Sample",
                "household_members": "4",
                "purpose": "Medical assistance",
                "date_issued": "2026-10-13",
            },
            "certificate_of_agreement": {
                "first_party": "Juan Dela Cruz",
                "second_party": "Maria Santos",
                "address": "Barangay Sample",
                "agreement_terms": "The parties agree to settle the matter.",
                "date_signed": "2026-10-13",
            },
            "cattle_clearance": {
                "owner_name": "Juan Dela Cruz",
                "address": "Barangay Sample",
                "cattle_count": "2",
                "cattle_description": "Two brown cattle",
                "origin": "Barangay Sample",
                "destination": "Town market",
                "transport_date": "2026-10-13",
            },
            "cutting_permit": {
                "applicant_name": "Juan Dela Cruz",
                "address": "Barangay Sample",
                "cutting_location": "Lot 12",
                "tree_species": "One mango tree",
                "reason": "Safety hazard",
                "proposed_date": "2026-10-13",
            },
            "conference_letter": {
                "addressee": "Juan Dela Cruz",
                "address": "Barangay Sample",
                "conference_subject": "Community matter",
                "conference_date": "2026-10-14",
                "conference_time": "09:00",
                "venue": "Barangay Hall",
                "letter_date": "2026-10-13",
            },
        }
        for app_name, label in DOCUMENTS:
            with self.subTest(document=label):
                form_response = self.client.get(reverse(f"{app_name}:create"))
                self.assertEqual(form_response.status_code, 200)
                print_response = self.client.post(
                    reverse(f"{app_name}:create"), post_data[app_name]
                )
                self.assertEqual(print_response.status_code, 200)
                self.assertContains(print_response, label.upper())
                self.assertContains(print_response, "DRAFT")
