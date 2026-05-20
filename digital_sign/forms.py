from django import forms
from .models import DigitalDocument
from .validators.file_validators import validate_pdf_file


class UploadPDFForm(forms.ModelForm):
    original_pdf = forms.FileField(
        validators=[validate_pdf_file],
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'application/pdf'
        })
    )

    class Meta:
        model = DigitalDocument
        fields = ['title', 'original_pdf']

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter document title'
            }),
        }


class VerifyPDFForm(forms.Form):
    pdf_file = forms.FileField(
        validators=[validate_pdf_file],
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'application/pdf'
        })
    )

    signature = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Paste the digital signature here'
        })
    )

    public_key = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Paste the public key here'
        })
    )