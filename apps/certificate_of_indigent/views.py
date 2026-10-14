from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import CertificateOfIndigentForm


@login_required
def create(request):
    form = CertificateOfIndigentForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        return render(request, "certificate_of_indigent/print.html", {"form": form})
    return render(request, "certificate_of_indigent/form.html", {"form": form})
