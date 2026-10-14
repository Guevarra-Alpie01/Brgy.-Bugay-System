from django import forms


class BarangayCertificateForm(forms.Form):
    full_name = forms.CharField(max_length=150, label="Resident's full name")
    address = forms.CharField(max_length=255)
    certified_information = forms.CharField(max_length=500, label="Information to certify")
    purpose = forms.CharField(max_length=255)
    date_issued = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
