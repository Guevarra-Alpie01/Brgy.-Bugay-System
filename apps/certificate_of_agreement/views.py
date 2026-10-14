from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import CertificateOfAgreementForm


@login_required
def create(request):
    form = CertificateOfAgreementForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        return render(request, "certificate_of_agreement/print.html", {"form": form})
    return render(request, "certificate_of_agreement/form.html", {"form": form})
