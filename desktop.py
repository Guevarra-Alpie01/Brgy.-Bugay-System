import logging
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


APP_TITLE = "Barangay Bugay System"
APP_HOST = "127.0.0.1"
APP_PORT = 8000
logger = logging.getLogger(__name__)


def app_root():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def app_data_dir():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise RuntimeError("Windows LOCALAPPDATA is not available.")
    return Path(local_app_data) / "BarangayBugaySystem"


def seed_existing_data(root, data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    target_database = data_dir / "db.sqlite3"
    target_media = data_dir / "media"
    for source_root in (root, root.parent):
        source_database = source_root / "db.sqlite3"
        if source_database.is_file() and not target_database.exists():
            shutil.copy2(source_database, target_database)

        source_media = source_root / "media"
        if source_media.is_dir() and not target_media.exists():
            shutil.copytree(source_media, target_media)


def ensure_django_secret(env_path):
    env_path.parent.mkdir(parents=True, exist_ok=True)
    values = {}
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    secret = values.get("DJANGO_SECRET_KEY")
    if not secret or len(secret) < 32 or "replace-with" in secret.lower():
        secret = secrets.token_urlsafe(48)
        values["DJANGO_SECRET_KEY"] = secret
        with env_path.open("w", encoding="utf-8", newline="\n") as env_file:
            for key, value in values.items():
                env_file.write(f"{key}={value}\n")
    return secret


def wait_for_service(url, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=2):
                return
        except (OSError, URLError):
            time.sleep(0.25)
    raise RuntimeError(
        "The local Django application did not start on port 8000. "
        "Close another program using that port and try again."
    )


def start_desktop():
    import django
    import webview
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from waitress import create_server

    root = app_root()
    data_dir = app_data_dir()
    seed_existing_data(root, data_dir)
    icon_path = root / "static" / "img" / "luffy.ico"
    if not icon_path.is_file():
        raise RuntimeError(f"The application icon is missing: {icon_path}")
    env_path = data_dir / ".env"
    django_secret = ensure_django_secret(env_path)
    os.environ["DJANGO_SECRET_KEY"] = django_secret
    os.environ["DJANGO_DEBUG"] = "false"
    os.environ["BRGY_DATA_DIR"] = str(data_dir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bugaysystem.settings")

    django.setup()
    call_command("migrate", interactive=False, verbosity=0)
    application = StaticFilesHandler(get_wsgi_application())
    try:
        server = create_server(
            application,
            host=APP_HOST,
            port=APP_PORT,
            threads=8,
        )
    except OSError as error:
        raise RuntimeError(
            "Could not start the local Django server on port 8000. "
            "Close the program using that port and retry."
        ) from error
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()
    try:
        wait_for_service(f"http://127.0.0.1:{APP_PORT}/accounts/login/")
        window = webview.create_window(
            APP_TITLE,
            f"http://127.0.0.1:{APP_PORT}/",
            width=1280,
            height=850,
            min_size=(960, 640),
            confirm_close=True,
        )
        webview.start(icon=str(icon_path))
    finally:
        server.close()
        server_thread.join(timeout=5)


def show_error(message):
    try:
        import tkinter
        from tkinter import messagebox
    except ImportError:
        print(f"{APP_TITLE}: {message}", file=sys.stderr)
        return
    try:
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror(APP_TITLE, message, parent=root)
        root.destroy()
    except tkinter.TclError as error:
        print(f"{APP_TITLE}: {message} ({error})", file=sys.stderr)


def main():
    try:
        start_desktop()
    except (ImportError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        show_error(str(error))
        raise


if __name__ == "__main__":
    main()
