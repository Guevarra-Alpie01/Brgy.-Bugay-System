from django import forms


class BarangayClearanceForm(forms.Form):
    full_name = forms.CharField(max_length=150, label="Resident's full name")
    address = forms.CharField(max_length=255)
    purpose = forms.CharField(max_length=255)
    years_of_residency = forms.CharField(max_length=50, required=False, label="Years of residency")
    date_issued = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
