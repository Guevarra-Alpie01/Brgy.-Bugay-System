from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import CuttingPermitForm


@login_required
def create(request):
    form = CuttingPermitForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        return render(request, "cutting_permit/print.html", {"form": form})
    return render(request, "cutting_permit/form.html", {"form": form})
