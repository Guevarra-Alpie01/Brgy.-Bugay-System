from django import forms


class ConferenceLetterForm(forms.Form):
    addressee = forms.CharField(max_length=150, label="Resident or party to notify")
    address = forms.CharField(max_length=255)
    conference_subject = forms.CharField(max_length=500, label="Conference subject")
    conference_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    conference_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    venue = forms.CharField(max_length=255, initial="Barangay Hall")
    letter_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
