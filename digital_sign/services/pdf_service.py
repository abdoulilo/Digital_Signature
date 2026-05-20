import os
import fitz
from django.conf import settings


def is_valid_pdf(file_path):
    try:
        with fitz.open(file_path) as pdf:
            return pdf.page_count > 0
    except Exception:
        return False


def create_signed_pdf_copy(document):
    """
    Creates a visible signed PDF copy.

    This does not create an Adobe-certified digital certificate signature.
    It creates a signed PDF copy containing:
    - file hash
    - digital signature
    - public key
    - signing status
    """

    original_path = document.original_pdf.path

    signed_dir = os.path.join(settings.MEDIA_ROOT, "pdfs", "signed")
    os.makedirs(signed_dir, exist_ok=True)

    original_filename = os.path.basename(document.original_pdf.name)
    signed_filename = f"signed_{document.id}_{original_filename}"
    signed_path = os.path.join(signed_dir, signed_filename)

    pdf = fitz.open(original_path)

    certificate_page = pdf.new_page(width=595, height=842)

    y = 70

    certificate_page.insert_text(
        (60, y),
        "Digital Signature Certificate",
        fontsize=22,
        fontname="helv",
    )

    y += 45

    certificate_page.insert_text(
        (60, y),
        f"Document Name: {document.filename()}",
        fontsize=11,
        fontname="helv",
    )

    y += 28

    certificate_page.insert_text(
        (60, y),
        f"Status: {document.status.upper()}",
        fontsize=11,
        fontname="helv",
    )

    y += 28

    certificate_page.insert_text(
        (60, y),
        "Algorithm: SHA-256 with RSA Signature",
        fontsize=11,
        fontname="helv",
    )

    y += 40

    certificate_page.insert_text(
        (60, y),
        "Document Hash:",
        fontsize=12,
        fontname="helv",
    )

    y += 22

    certificate_page.insert_textbox(
        fitz.Rect(60, y, 535, y + 70),
        document.file_hash or "",
        fontsize=9,
        fontname="cour",
    )

    y += 95

    certificate_page.insert_text(
        (60, y),
        "Digital Signature:",
        fontsize=12,
        fontname="helv",
    )

    y += 22

    certificate_page.insert_textbox(
        fitz.Rect(60, y, 535, y + 140),
        document.signature or "",
        fontsize=8,
        fontname="cour",
    )

    y += 165

    certificate_page.insert_text(
        (60, y),
        "Public Key:",
        fontsize=12,
        fontname="helv",
    )

    y += 22

    certificate_page.insert_textbox(
        fitz.Rect(60, y, 535, y + 170),
        document.public_key or "",
        fontsize=7,
        fontname="cour",
    )

    pdf.save(signed_path)
    pdf.close()

    return f"pdfs/signed/{signed_filename}"