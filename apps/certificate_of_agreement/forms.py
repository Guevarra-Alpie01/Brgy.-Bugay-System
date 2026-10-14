from django import forms


class CertificateOfAgreementForm(forms.Form):
    first_party = forms.CharField(max_length=150)
    second_party = forms.CharField(max_length=150)
    address = forms.CharField(max_length=255, label="Parties' address")
    agreement_terms = forms.CharField(max_length=2000, widget=forms.Textarea, label="Agreement terms")
    date_signed = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
