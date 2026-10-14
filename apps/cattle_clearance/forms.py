from django import forms


class CattleClearanceForm(forms.Form):
    owner_name = forms.CharField(max_length=150, label="Owner's full name")
    address = forms.CharField(max_length=255)
    cattle_count = forms.IntegerField(min_value=1, label="Number of cattle")
    cattle_description = forms.CharField(max_length=500, widget=forms.Textarea)
    origin = forms.CharField(max_length=255)
    destination = forms.CharField(max_length=255)
    transport_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
