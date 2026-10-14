from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .forms import ConferenceLetterForm


@login_required
def create(request):
    form = ConferenceLetterForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        return render(request, "conference_letter/print.html", {"form": form})
    return render(request, "conference_letter/form.html", {"form": form})
