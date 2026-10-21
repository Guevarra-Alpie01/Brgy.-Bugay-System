import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from desktop import ensure_django_secret, seed_existing_data


class DesktopLauncherTests(TestCase):
    def test_first_launch_creates_private_django_secret(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / "data" / ".env"

            secret = ensure_django_secret(env_path)

            self.assertGreaterEqual(len(secret), 32)
            self.assertIn(f"DJANGO_SECRET_KEY={secret}", env_path.read_text(encoding="utf-8"))
            self.assertNotIn("ONLYOFFICE", env_path.read_text(encoding="utf-8"))

    def test_generated_secret_is_preserved_between_launches(self):
        with TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            first = ensure_django_secret(env_path)
            second = ensure_django_secret(env_path)

            self.assertEqual(first, second)

    def test_existing_project_data_is_seeded_once_without_overwrite(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "project"
            data_dir = Path(temp_dir) / "app-data"
            (root / "media").mkdir(parents=True)
            (root / "db.sqlite3").write_bytes(b"existing database")
            (root / "media" / "upload.docx").write_bytes(b"existing upload")

            seed_existing_data(root, data_dir)

            self.assertEqual((data_dir / "db.sqlite3").read_bytes(), b"existing database")
            self.assertEqual(
                (data_dir / "media" / "upload.docx").read_bytes(),
                b"existing upload",
            )
            (data_dir / "db.sqlite3").write_bytes(b"new database")
            seed_existing_data(root, data_dir)
            self.assertEqual((data_dir / "db.sqlite3").read_bytes(), b"new database")

    @patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\Staff\\AppData\\Local"})
    def test_app_data_is_scoped_to_current_windows_user(self):
        from desktop import app_data_dir

        self.assertEqual(
            app_data_dir(),
            Path("C:/Users/Staff/AppData/Local/BarangayBugaySystem"),
        )
