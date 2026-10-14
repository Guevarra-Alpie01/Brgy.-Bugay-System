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
from django.shortcuts import render
from django.urls import include, path


@login_required
def home(request):
    documents = [
        ("Barangay Clearance", "barangay_clearance:create"),
        ("Barangay Certificate", "barangay_certificate:create"),
        ("Certificate of Indigent", "certificate_of_indigent:create"),
        ("Certificate of Agreement", "certificate_of_agreement:create"),
        ("Cattle Clearance", "cattle_clearance:create"),
        ("Cutting Permit", "cutting_permit:create"),
        ("Conference Letter", "conference_letter:create"),
    ]
    return render(request, "home.html", {"documents": documents})

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
    path('barangay-clearance/', include('apps.barangay_clearance.urls')),
    path('barangay-certificate/', include('apps.barangay_certificate.urls')),
    path('certificate-of-indigent/', include('apps.certificate_of_indigent.urls')),
    path('certificate-of-agreement/', include('apps.certificate_of_agreement.urls')),
    path('cattle-clearance/', include('apps.cattle_clearance.urls')),
    path('cutting-permit/', include('apps.cutting_permit.urls')),
    path('conference-letter/', include('apps.conference_letter.urls')),
]
