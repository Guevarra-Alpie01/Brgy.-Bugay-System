from django import forms

from .models import UploadedDocument


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedDocument
        fields = ("category", "file")
        widgets = {
            "category": forms.Select(attrs={"required": True}),
            "file": forms.ClearableFileInput(attrs={"required": True}),
        }

    def save(self, commit=True):
        uploaded_document = super().save(commit=False)
        uploaded_document.original_name = self.cleaned_data["file"].name
        if commit:
            uploaded_document.save()
            self.save_m2m()
        return uploaded_document
