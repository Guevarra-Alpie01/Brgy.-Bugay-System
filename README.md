# Barangay Bugay System

## Local Office editing and printing

Word, Excel, and PowerPoint uploads are opened in the embedded ONLYOFFICE
editor. The editor can save changes back to the uploaded file and print it;
the editor's download permission is disabled. PDF and common image uploads
open in the browser. Other file types are not offered as downloads.

ONLYOFFICE Docs runs locally in Docker, so editing works without an internet
connection after Docker has downloaded the image. The host computer must
meet ONLYOFFICE's requirements (at least 4 GB RAM is recommended). Docker
Desktop and its Linux/WSL 2 backend must be installed and running.

1. Copy `.env.example` to `.env` and replace `ONLYOFFICE_JWT_SECRET` with a
   long random value. For example, in PowerShell:

   ```powershell
   Copy-Item .env.example .env
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Put the generated value in `.env`. Keep `.env` private; it is ignored by
   Git.
2. Start ONLYOFFICE Docs and wait for its first-time startup:

   ```powershell
   docker compose up -d
   ```

3. Start the Django app with `run_django.bat`. This reads the same `.env`
   values and exposes the app on port 8000 so the local editor container can
   retrieve and save files.
4. Sign in, open one of the seven document categories, and click a Word,
   Excel, or PowerPoint file. Use the editor's Print command to print it.

The default configuration is for using the app and ONLYOFFICE on the same
computer. If other computers on a local network will use the app, configure
`ONLYOFFICE_DOCUMENT_SERVER_URL` and `ONLYOFFICE_BACKEND_URL` in `.env` with
addresses reachable from those computers and from the ONLYOFFICE container.
Allow the configured ports through the local firewall. Do not expose the
Django development server or the editor to the public internet.
