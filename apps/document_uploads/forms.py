from django import forms
from django.core.exceptions import ValidationError

from .models import UploadedDocument


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedDocument
        fields = ("category", "file")
        widgets = {
            "category": forms.Select(attrs={"required": True}),
            "file": forms.ClearableFileInput(attrs={"required": True}),
        }

    def clean_file(self):
        uploaded_files = self.files.getlist(self.add_prefix("file"))
        if len(uploaded_files) > 1:
            raise ValidationError("Upload one file at a time.")
        return self.cleaned_data["file"]

    def clean_category(self):
        category = self.cleaned_data["category"]
        if UploadedDocument.objects.filter(category=category).exists():
            raise ValidationError(
                "This classification already has a file. Delete it before uploading another."
            )
        return category

    def save(self, commit=True):
        uploaded_document = super().save(commit=False)
        uploaded_document.original_name = self.cleaned_data["file"].name
        if commit:
            uploaded_document.save()
            self.save_m2m()
        return uploaded_document
