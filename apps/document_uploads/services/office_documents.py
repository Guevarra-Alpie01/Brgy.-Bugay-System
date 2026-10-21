import logging
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation, ValidationError

from apps.document_uploads.models import UploadedDocument

logger = logging.getLogger(__name__)

OFFICE_FILE_TYPES = {
    ".doc": "word",
    ".docm": "word",
    ".docx": "word",
    ".xls": "excel",
    ".xlsm": "excel",
    ".xlsx": "excel",
}
OFFICE_EXECUTABLES = {"word": "WINWORD.EXE", "excel": "EXCEL.EXE"}
NEW_FILE_EXTENSIONS = {"word": ".docx", "excel": ".xlsx"}


def file_location(document):
    try:
        root = Path(settings.MEDIA_ROOT).resolve(strict=True)
        path = Path(document.file.path).resolve(strict=True)
    except (OSError, ValueError, SuspiciousFileOperation) as error:
        raise ValidationError("The document file is missing or unavailable.") from error
    if not path.is_file() or not path.is_relative_to(root):
        raise ValidationError("The document is outside the application file store.")
    return path


def launch_document(document, popen=None):
    extension = Path(document.original_name).suffix.lower()
    office_kind = OFFICE_FILE_TYPES.get(extension)
    if not office_kind:
        raise ValidationError("This document type cannot be opened in Word or Excel.")
    path = file_location(document)
    executable = find_office_executable(office_kind)
    try:
        (popen or subprocess.Popen)([str(executable), str(path)], shell=False)
    except OSError as error:
        logger.exception("Could not launch Office for document %s.", document.pk)
        raise RuntimeError(
            f"Microsoft {office_kind.title()} could not open this document."
        ) from error
    return f"Opened {document.original_name} in Microsoft {office_kind.title()}."


def find_office_executable(office_kind):
    executable_name = OFFICE_EXECUTABLES[office_kind]
    candidates = []
    if sys.platform == "win32":
        candidates.extend(_registry_office_paths(executable_name))

    for root_name in ("ProgramFiles", "ProgramFiles(x86)"):
        root = os.environ.get(root_name)
        if root:
            for version in ("Office16", "Office15", "Office14"):
                candidates.append(Path(root) / "Microsoft Office" / "root" / version / executable_name)
                candidates.append(Path(root) / "Microsoft Office" / version / executable_name)

    path_executable = shutil.which(executable_name)
    if path_executable:
        candidates.append(Path(path_executable))

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError(
        f"Microsoft {office_kind.title()} is not installed or its executable "
        "could not be found. Install the desktop Office application and retry."
    )


def _registry_office_paths(executable_name):
    try:
        import winreg
    except ImportError:
        return []

    candidates = []
    hives = (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE)
    views = (0, getattr(winreg, "KEY_WOW64_64KEY", 0), getattr(winreg, "KEY_WOW64_32KEY", 0))
    for hive in hives:
        for view in views:
            key_path = rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{executable_name}"
            try:
                with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ | view) as key:
                    value, _ = winreg.QueryValueEx(key, None)
            except OSError:
                continue
            if value:
                candidates.append(Path(value.strip().strip('"')))
    return candidates


def create_new_document(category, office_kind, ask_save_path=None, launch=True):
    if office_kind not in NEW_FILE_EXTENSIONS:
        raise ValidationError("Choose Word or Excel for a new document.")
    _validate_category(category)
    if launch:
        find_office_executable(office_kind)
    extension = NEW_FILE_EXTENSIONS[office_kind]
    destination = ask_save_path(category, extension) if ask_save_path else None
    if not destination:
        return "Cancelled."
    destination = _validate_destination(destination, category, extension)
    if destination.exists() or UploadedDocument.objects.filter(
        category=category,
        original_name=destination.name,
    ).exists():
        raise FileExistsError("A file with that name already exists.")

    try:
        _write_blank_openxml(destination, office_kind)
        document = _record_existing_file(destination, category)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    if launch:
        try:
            launch_document(document)
        except Exception:
            document.delete()
            destination.unlink(missing_ok=True)
            raise
    return f"Created {destination.name} and opened it in Microsoft Office."


def save_as_document(document, ask_save_path, launch=True):
    source = file_location(document)
    extension = source.suffix.lower()
    if extension not in OFFICE_FILE_TYPES:
        raise ValidationError("Only Word and Excel files can be saved as another copy.")
    if launch:
        find_office_executable(OFFICE_FILE_TYPES[extension])
    destination = ask_save_path(document.category, extension, document.original_name)
    if not destination:
        return "Cancelled."
    destination = _validate_destination(destination, document.category, extension)
    if destination.exists() or UploadedDocument.objects.filter(
        category=document.category,
        original_name=destination.name,
    ).exists():
        raise FileExistsError("A file with that name already exists.")
    try:
        shutil.copy2(source, destination)
        copied_document = _record_existing_file(
            destination,
            document.category,
            uploaded_by=document.uploaded_by,
        )
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    if launch:
        try:
            launch_document(copied_document)
        except Exception:
            copied_document.delete()
            destination.unlink(missing_ok=True)
            raise
    return f"Created a separate copy, {destination.name}, and opened it."


def rename_document(document, new_name):
    source = file_location(document)
    clean_name = _validate_filename(new_name)
    extension = Path(clean_name).suffix.lower()
    if extension != source.suffix.lower():
        raise ValidationError("Renaming cannot change the document file type.")
    if extension not in OFFICE_FILE_TYPES:
        raise ValidationError("This document type is not supported.")
    if clean_name == document.original_name:
        return document
    if UploadedDocument.objects.filter(
        category=document.category,
        original_name=clean_name,
    ).exclude(pk=document.pk).exists():
        raise FileExistsError("A document with that name already exists here.")
    destination = source.with_name(clean_name)
    if destination.exists():
        raise FileExistsError("A file with that name already exists here.")
    source.rename(destination)
    try:
        relative_name = destination.relative_to(Path(settings.MEDIA_ROOT).resolve()).as_posix()
        document.file.name = relative_name
        document.original_name = clean_name
        document.save(update_fields=("file", "original_name"))
    except Exception:
        destination.rename(source)
        raise
    return document


def delete_document(document):
    path = file_location(document)
    path.unlink()
    document.delete()


def cleanup_orphaned_document_files():
    media_root = Path(settings.MEDIA_ROOT).resolve()
    document_root = (media_root / "document_uploads").resolve()
    if not document_root.is_relative_to(media_root):
        raise ValidationError("The document storage path is outside the media directory.")
    if not document_root.is_dir():
        return 0

    referenced_files = set(
        UploadedDocument.objects.values_list("file", flat=True)
    )
    removed_count = 0
    failures = []

    for path in document_root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            resolved_path = path.resolve(strict=True)
            if not resolved_path.is_relative_to(document_root):
                continue
            relative_path = resolved_path.relative_to(media_root).as_posix()
            if relative_path in referenced_files:
                continue
            resolved_path.unlink()
            removed_count += 1
        except OSError as error:
            logger.exception("Could not clean up orphaned document file %s.", path)
            failures.append(error)

    if failures:
        raise OSError(
            f"Removed {removed_count} orphaned files, but could not remove "
            f"{len(failures)} other file(s)."
        ) from failures[0]
    return removed_count


def _record_existing_file(path, category, uploaded_by=None):
    media_root = Path(settings.MEDIA_ROOT).resolve()
    relative_name = path.resolve().relative_to(media_root).as_posix()
    return UploadedDocument.objects.create(
        category=category,
        file=relative_name,
        original_name=path.name,
        uploaded_by=uploaded_by,
    )


def _validate_category(category):
    if category not in dict(UploadedDocument._meta.get_field("category").choices):
        raise ValidationError("Unknown document category.")


def _validate_filename(name):
    if not isinstance(name, str):
        raise ValidationError("Enter a valid filename.")
    clean_name = name.strip()
    if (
        not clean_name
        or clean_name in {".", ".."}
        or Path(clean_name).name != clean_name
        or any(char in clean_name for char in '<>:"/\\|?*')
        or any(ord(char) < 32 for char in clean_name)
    ):
        raise ValidationError("Enter a filename without folder paths or invalid characters.")
    return clean_name


def _validate_destination(destination, category, expected_extension):
    _validate_category(category)
    root = Path(settings.MEDIA_ROOT).resolve()
    category_root = (root / "document_uploads" / category).resolve()
    path = Path(destination).expanduser().resolve()
    if not path.is_relative_to(category_root):
        raise ValidationError("Choose a location inside this document category.")
    clean_name = _validate_filename(path.name)
    if Path(clean_name).suffix.lower() != expected_extension:
        raise ValidationError(f"Use the {expected_extension} file extension.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _write_blank_openxml(path, office_kind):
    if office_kind == "word":
        parts = {
            "[Content_Types].xml": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                '</Types>'
            ),
            "_rels/.rels": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                '</Relationships>'
            ),
            "word/document.xml": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                '<w:body><w:p/><w:sectPr/></w:body></w:document>'
            ),
        }
    else:
        parts = {
            "[Content_Types].xml": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                '</Types>'
            ),
            "_rels/.rels": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                '</Relationships>'
            ),
            "xl/workbook.xml": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
            ),
            "xl/_rels/workbook.xml.rels": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                '</Relationships>'
            ),
            "xl/worksheets/sheet1.xml": (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData/></worksheet>'
            ),
        }
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in parts.items():
            archive.writestr(name, content)
