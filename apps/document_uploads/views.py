import json
import logging
import mimetypes
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode, urlparse
from urllib.request import urlopen

import jwt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.files.base import ContentFile
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import DOCUMENT_CATEGORIES, UploadedDocument

logger = logging.getLogger(__name__)

OFFICE_TYPES = {
    ".doc": "word",
    ".docm": "word",
    ".docx": "word",
    ".dot": "word",
    ".dotm": "word",
    ".dotx": "word",
    ".odt": "word",
    ".ott": "word",
    ".rtf": "word",
    ".txt": "word",
    ".xls": "cell",
    ".xlsb": "cell",
    ".xlsm": "cell",
    ".xlsx": "cell",
    ".xlt": "cell",
    ".xltm": "cell",
    ".xltx": "cell",
    ".ods": "cell",
    ".ots": "cell",
    ".csv": "cell",
    ".ppt": "slide",
    ".pptm": "slide",
    ".pptx": "slide",
    ".pps": "slide",
    ".ppsx": "slide",
    ".odp": "slide",
    ".otp": "slide",
}
INLINE_TYPES = {
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".webp": "image/webp",
}
FILE_TOKEN_SALT = "document-uploads-file"
CALLBACK_TOKEN_SALT = "document-uploads-callback"
TOKEN_MAX_AGE = 24 * 60 * 60


@login_required
def category_files(request, category):
    category_names = dict(DOCUMENT_CATEGORIES)
    if category not in category_names:
        raise Http404("Document category not found.")

    documents = UploadedDocument.objects.filter(category=category)
    return render(
        request,
        "document_uploads/category_files.html",
        {
            "category": category,
            "category_name": category_names[category],
            "documents": documents,
        },
    )


@login_required
def view_file(request, pk):
    document = get_object_or_404(UploadedDocument, pk=pk)
    extension = Path(document.original_name).suffix.lower()
    if extension in OFFICE_TYPES:
        file_token = signing.dumps({"pk": document.pk}, salt=FILE_TOKEN_SALT)
        callback_token = signing.dumps(
            {"pk": document.pk},
            salt=CALLBACK_TOKEN_SALT,
        )
        content_url = (
            settings_url(
                reverse("document_uploads:content", args=[document.pk])
            )
            + "?"
            + urlencode({"token": file_token})
        )
        callback_url = (
            settings_url(
                reverse("document_uploads:callback", args=[document.pk])
            )
            + "?"
            + urlencode({"token": callback_token})
        )
        editor_config = {
            "documentType": OFFICE_TYPES[extension],
            "document": {
                "fileType": extension[1:],
                "key": f"{document.pk}-{document.revision}",
                "title": document.original_name,
                "url": content_url,
                "permissions": {
                    "edit": True,
                    "download": False,
                    "print": True,
                },
            },
            "editorConfig": {
                "mode": "edit",
                "callbackUrl": callback_url,
                "user": {
                    "id": str(request.user.pk),
                    "name": request.user.get_username(),
                },
                "customization": {"forcesave": True},
            },
        }
        editor_config["token"] = jwt.encode(
            editor_config,
            settings.ONLYOFFICE_JWT_SECRET,
            algorithm="HS256",
        )
        return render(
            request,
            "document_uploads/office_editor.html",
            {
                "document": document,
                "category": document.category,
                "category_name": dict(DOCUMENT_CATEGORIES)[document.category],
                "editor_config": editor_config,
                "onlyoffice_api_url": (
                    settings.ONLYOFFICE_DOCUMENT_SERVER_URL
                    + "/web-apps/apps/api/documents/api.js"
                ),
            },
        )

    content_type = INLINE_TYPES.get(extension)
    if content_type is None and extension in {".csv", ".txt"}:
        content_type = "text/plain; charset=utf-8"
    if content_type is None:
        return render(
            request,
            "document_uploads/unsupported_file.html",
            {"document": document},
            status=415,
        )

    response = FileResponse(
        document.file.open("rb"),
        as_attachment=False,
        filename=document.original_name,
        content_type=content_type,
    )
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = "inline"
    return response


def settings_url(path):
    return f"{settings.ONLYOFFICE_BACKEND_URL}{path}"


def document_content(request, pk):
    document = get_object_or_404(UploadedDocument, pk=pk)
    try:
        token_data = signing.loads(
            request.GET.get("token", ""),
            salt=FILE_TOKEN_SALT,
            max_age=TOKEN_MAX_AGE,
        )
    except signing.BadSignature:
        raise Http404("Document link is invalid or expired.")
    if token_data != {"pk": document.pk}:
        raise Http404("Document link is invalid or expired.")

    content_type = mimetypes.guess_type(document.original_name)[0]
    response = FileResponse(
        document.file.open("rb"),
        as_attachment=False,
        content_type=content_type or "application/octet-stream",
    )
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Disposition"] = "inline"
    return response


@csrf_exempt
def editor_callback(request, pk):
    if request.method != "POST":
        return JsonResponse({"error": 1}, status=405)

    document = get_object_or_404(UploadedDocument, pk=pk)
    try:
        token_data = signing.loads(
            request.GET.get("token", ""),
            salt=CALLBACK_TOKEN_SALT,
            max_age=TOKEN_MAX_AGE,
        )
        if token_data != {"pk": document.pk}:
            return JsonResponse({"error": 1}, status=403)
        payload = json.loads(request.body)
        authorization = request.headers.get("Authorization", "")
        jwt_token = authorization.removeprefix("Bearer ").strip()
        claims = jwt.decode(
            jwt_token,
            settings.ONLYOFFICE_JWT_SECRET,
            algorithms=["HS256"],
        )
        if claims.get("payload", claims) != payload:
            return JsonResponse({"error": 1}, status=403)
    except (signing.BadSignature, jwt.InvalidTokenError, json.JSONDecodeError):
        return JsonResponse({"error": 1}, status=403)

    if payload.get("key") != f"{document.pk}-{document.revision}":
        return JsonResponse({"error": 1}, status=409)

    if payload.get("status") in (2, 6):
        download_url = payload.get("url")
        if not isinstance(download_url, str) or not _is_document_server_url(
            download_url
        ):
            return JsonResponse({"error": 1}, status=400)
        try:
            with urlopen(download_url, timeout=60) as saved_file:
                content = saved_file.read()
        except (OSError, URLError, TimeoutError):
            logger.exception("Could not retrieve edited file %s.", document.pk)
            return JsonResponse({"error": 1}, status=502)

        try:
            previous_file_name = document.file.name
            document.file.save(
                Path(document.original_name).name,
                ContentFile(content),
                save=False,
            )
            document.revision += 1
            document.save(update_fields=("file", "revision"))
        except OSError:
            logger.exception("Could not store edited file %s.", document.pk)
            return JsonResponse({"error": 1}, status=500)
        if previous_file_name != document.file.name:
            try:
                document.file.storage.delete(previous_file_name)
            except OSError:
                logger.exception(
                    "Could not remove the previous version of file %s.",
                    document.pk,
                )

    return JsonResponse({"error": 0})


def _is_document_server_url(url):
    parsed_url = urlparse(url)
    document_server_host = urlparse(
        settings.ONLYOFFICE_DOCUMENT_SERVER_URL
    ).hostname
    return (
        parsed_url.scheme in {"http", "https"}
        and parsed_url.hostname
        in {
            document_server_host,
            "localhost",
            "host.docker.internal",
        }
    )
