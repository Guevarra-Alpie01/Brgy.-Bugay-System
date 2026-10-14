from django import forms


class CertificateOfIndigentForm(forms.Form):
    full_name = forms.CharField(max_length=150, label="Resident's full name")
    address = forms.CharField(max_length=255)
    household_members = forms.IntegerField(min_value=1, label="Number of household members")
    purpose = forms.CharField(max_length=255)
    date_issued = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
