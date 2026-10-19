"""
URL configuration for bugaysystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import include, path

from apps.document_uploads.forms import DocumentUploadForm
from apps.document_uploads.models import DOCUMENT_CATEGORIES, UploadedDocument


@login_required
def home(request):
    form = DocumentUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        uploaded_document = form.save(commit=False)
        uploaded_document.uploaded_by = request.user
        uploaded_document.save()
        messages.success(request, "File uploaded successfully.")
        return redirect("home")

    uploads_by_category = {category: [] for category, _ in DOCUMENT_CATEGORIES}
    for uploaded_document in UploadedDocument.objects.order_by("-uploaded_at"):
        uploads_by_category[uploaded_document.category].append(uploaded_document)

    category_urls = {
        "barangay-clearance": "barangay_clearance:create",
        "barangay-certificate": "barangay_certificate:create",
        "certificate-of-indigent": "certificate_of_indigent:create",
        "certificate-of-agreement": "certificate_of_agreement:create",
        "cattle-clearance": "cattle_clearance:create",
        "cutting-permit": "cutting_permit:create",
        "conference-letter": "conference_letter:create",
    }
    documents = [
        (name, category_urls[category], category, uploads_by_category[category])
        for category, name in DOCUMENT_CATEGORIES
    ]

    return render(
        request,
        "home.html",
        {
            "documents": documents,
            "upload_form": form,
        },
    )

urlpatterns = [
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('uploads/', include('apps.document_uploads.urls')),
    path('barangay-clearance/', include('apps.barangay_clearance.urls')),
    path('barangay-certificate/', include('apps.barangay_certificate.urls')),
    path('certificate-of-indigent/', include('apps.certificate_of_indigent.urls')),
    path('certificate-of-agreement/', include('apps.certificate_of_agreement.urls')),
    path('cattle-clearance/', include('apps.cattle_clearance.urls')),
    path('cutting-permit/', include('apps.cutting_permit.urls')),
    path('conference-letter/', include('apps.conference_letter.urls')),
]
