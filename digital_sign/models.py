from django.db import models
from django.contrib.auth.models import User


class DigitalDocument(models.Model):
    STATUS_CHOICES = [
    ('uploaded', 'Uploaded'),
    ('hashed', 'Hash Generated'),
    ('signed', 'Signed'),
    ('verified', 'Verified'),
    ('failed', 'Failed'),
]

    title = models.CharField(max_length=255, blank=True)
    original_pdf = models.FileField(upload_to='pdfs/original/')
    signed_pdf = models.FileField(upload_to='pdfs/signed/', blank=True, null=True)

    file_hash = models.CharField(max_length=128, blank=True)
    signature = models.TextField(blank=True)

    public_key = models.TextField(blank=True)
    private_key = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    verification_message = models.TextField(blank=True)

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def filename(self):
        return self.original_pdf.name.split('/')[-1]

    def __str__(self):
        return self.title or self.filename()