from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import BarangayCertificateForm


@login_required
def create(request):
    form = BarangayCertificateForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        return render(request, "barangay_certificate/print.html", {"form": form})
    return render(request, "barangay_certificate/form.html", {"form": form})
