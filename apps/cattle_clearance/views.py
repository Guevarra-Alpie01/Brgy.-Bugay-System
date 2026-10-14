from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import CattleClearanceForm


@login_required
def create(request):
    form = CattleClearanceForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        return render(request, "cattle_clearance/print.html", {"form": form})
    return render(request, "cattle_clearance/form.html", {"form": form})
