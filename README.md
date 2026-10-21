# Barangay Bugay System

## Windows desktop app

The desktop launcher runs Django locally with Waitress and displays it in a
PyWebView window. Word and Excel documents are opened with the installed
Microsoft Office desktop applications; the app does not implement its own
Office editor. PDF and image uploads remain viewable in the app.

The local server listens only on `127.0.0.1:8000`. SQLite data, uploaded
documents, and the generated Django secret are stored in:

```text
%LOCALAPPDATA%\BarangayBugaySystem
```

On first launch, an existing project-root `db.sqlite3` and `media` directory
are copied into that data folder only if the corresponding app-data item does
not already exist. The app does not replace existing data during updates.

### Requirements

- 64-bit Windows 11 (Windows 7 and Docker-based deployment are not supported
  by this configuration).
- Python 3.13, 64-bit. Install from
  [python.org](https://www.python.org/downloads/windows/).
- Microsoft Word and Excel desktop applications installed and licensed on
  each PC where those file types will be edited. Office is a separate
  Microsoft product; this project does not include or license it.
- Microsoft Edge WebView2 Runtime. Windows 11 commonly includes it; install
  the [Evergreen Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)
  if it is missing.

This application does not require Docker, WSL, or an internet connection
after Python dependencies and Office have been installed. Each PC has its own
independent local database and media folder. At runtime the app uses its
locally served templates, CSS, JavaScript, and images; it does not load
remote fonts, CDN scripts/styles, cloud editors, or external APIs. Office
licensing or first-time activation may have separate Microsoft requirements.

### Install and run

In PowerShell, from the project directory:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\create_desktop_shortcut.ps1
```

Double-click the **Barangay Bugay System** desktop shortcut or run
`run_desktop.bat`. The launcher creates `%LOCALAPPDATA%\BarangayBugaySystem`,
migrates its SQLite database, and starts the local desktop window. Close the
app after its first launch, then create the initial sign-in account in the
same app-data database:

```powershell
$env:BRGY_DATA_DIR = "$env:LOCALAPPDATA\BarangayBugaySystem"
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
Remove-Item Env:\BRGY_DATA_DIR
```

If you already have a project-root database/media directory, the launcher
copies it to app data on first launch. If that database already contains a
sign-in account, you can skip creating another one.
The desktop shortcut created by `create_desktop_shortcut.ps1` is named
**Luffy** and uses the icon at `static\img\luffy.ico`.

### Working with documents

Click one of the seven classification cards to open its newest uploaded file.
Word and Excel documents launch directly in the matching Microsoft Office
desktop app without conversion; Office handles editing, saving, and printing.
Supported Office extensions are `.doc`, `.docx`, `.docm`, `.xls`, `.xlsx`,
and `.xlsm`.

- The home screen's folder icon opens all uploads grouped by classification;
  each file has a confirmation-protected delete control beside it.
- Each home-screen classification heading opens its newest uploaded file
  directly (launching Word or Excel for Office documents). For categories
  with no uploads, the heading opens that category's page; use the folder icon
  to browse all uploaded files.

Excel and Word handle supported format features and any compatibility
warnings. Macro-enabled `.docm` and `.xlsm` files are launched in Office
without conversion; Office may show its usual security prompts. A supported
Office installation is required to use native editing/printing features.
Use the local desktop app so Office opens on the same PC as the application.

PDFs and common image files can be viewed in the application. PDF is not
edited by this integration; use an installed PDF editor if editing is needed.
Printing PDFs is through the browser's PDF viewer. Other unsupported file
types are kept in storage but cannot be previewed or opened through these
controls.

### Offline installation on another PC

Prepare the project and Python dependencies on a trusted machine with the
same Windows architecture and Python version as the target. Copy the source
folder and a Python wheelhouse to removable storage. For example:

```powershell
.\.venv\Scripts\python.exe -m pip download --dest wheelhouse -r requirements.txt
```

Copy the project directory and `wheelhouse` to the target PC, install Python,
Office, and WebView2 there, then install dependencies without network access:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --find-links .\wheelhouse -r requirements.txt
.\create_desktop_shortcut.ps1
```

Launch the app once, close it, then run the `BRGY_DATA_DIR` migration and
`createsuperuser` commands shown above if this PC has no existing account.
The wheelhouse must contain wheels compatible with the target's Windows
architecture and CPython version. Keep personal database/media backups
separate from application source and transfer them only to authorized PCs.
No Docker image or Docker installer is part of the distribution.

### Backup, updates, and troubleshooting

Close the app before backing up or updating. Back up both:

```text
%LOCALAPPDATA%\BarangayBugaySystem\db.sqlite3
%LOCALAPPDATA%\BarangayBugaySystem\media
```

Do not overwrite the app-data folder when replacing application files. The
launcher applies database migrations on startup. Keep backups of the database
and media before applying updates.

- If the desktop window does not open, run `run_desktop.bat` from the project
  folder to see the startup error.
- If port 8000 is already in use, close the other local program and relaunch.
  The app does not bind to the LAN.
- If Word or Excel is reported as missing, install the corresponding desktop
  Office application, then restart the app.
- If an Office file cannot be opened, check its extension, file permissions,
  and whether Office has locked it in another window.
- If a saved document appears unchanged in the list, use **Refresh**. The
  file's modified timestamp is read from disk.
- Keep `.env` and the app-data folder private. Do not place secrets in source
  control or distribute another PC's generated `.env`.

## Development

Install the same requirements, then run the local development server:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```
