import os
from django.core.exceptions import ValidationError


def validate_pdf_file(file):
    ext = os.path.splitext(file.name)[1].lower()

    if ext != '.pdf':
        raise ValidationError('Only PDF files are allowed.')

    max_size = 10 * 1024 * 1024  # 10 MB

    if file.size > max_size:
        raise ValidationError('PDF file size must not exceed 10 MB.')