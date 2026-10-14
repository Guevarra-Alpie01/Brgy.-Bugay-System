from django import forms


class CuttingPermitForm(forms.Form):
    applicant_name = forms.CharField(max_length=150)
    address = forms.CharField(max_length=255)
    cutting_location = forms.CharField(max_length=255)
    tree_species = forms.CharField(max_length=255, label="Tree species and number")
    reason = forms.CharField(max_length=1000, widget=forms.Textarea)
    proposed_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
