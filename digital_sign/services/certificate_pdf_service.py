import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


def _get_filename(certificate):
    if hasattr(certificate, "filename"):
        filename_attr = certificate.filename
        if callable(filename_attr):
            return filename_attr()
        return filename_attr

    if getattr(certificate, "original_pdf", None):
        return certificate.original_pdf.name.split("/")[-1]

    return "Uploaded PDF"


def _get_file_hash(certificate):
    return getattr(certificate, "file_hash", "") or getattr(certificate, "document_hash", "") or ""


def _get_document_code(certificate):
    if hasattr(certificate, "document_id") and getattr(certificate, "document_id"):
        return str(certificate.document_id)

    return f"DS-{certificate.id:06d}"


def generate_certificate_pdf(certificate, verify_url: str, qr_png: bytes) -> bytes:
    """
    Generate a separate one-page digital certificate PDF.
    """
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    document_code = _get_document_code(certificate)
    file_name = _get_filename(certificate)
    file_hash = _get_file_hash(certificate)
    signed_at = getattr(certificate, "signed_at", None)

    pdf.setTitle(f"Digital Certificate - {document_code}")

    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 35 * mm, "Digital Verification Certificate")

    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(
        width / 2,
        height - 45 * mm,
        "Use this certificate to verify that the PDF matches the signed record.",
    )

    qr_size = 62 * mm
    qr_x = (width - qr_size) / 2
    qr_y = height - 125 * mm

    qr_image = ImageReader(io.BytesIO(qr_png))
    pdf.drawImage(
        qr_image,
        qr_x,
        qr_y,
        qr_size,
        qr_size,
        preserveAspectRatio=True,
        mask="auto",
    )

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawCentredString(width / 2, qr_y - 10 * mm, "Scan to verify authenticity")

    y = qr_y - 30 * mm
    left = 35 * mm
    value_x = left + 38 * mm

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left, y, "Document ID:")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(value_x, y, document_code)

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left, y - 10 * mm, "Filename:")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(value_x, y - 10 * mm, file_name[:72])

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left, y - 20 * mm, "Fingerprint:")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(value_x, y - 20 * mm, f"{file_hash[:42]}..." if file_hash else "Not available")

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left, y - 30 * mm, "Status:")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(value_x, y - 30 * mm, "Digitally signed")

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left, y - 40 * mm, "Signed at:")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(value_x, y - 40 * mm, str(signed_at) if signed_at else "Not available")

    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left, y - 52 * mm, "How to verify:")
    pdf.setFont("Helvetica", 9)
    pdf.drawString(value_x, y - 52 * mm, "Scan the QR code above to open the verification page.")
    pdf.drawString(value_x, y - 58 * mm, "Then upload the PDF to confirm it matches this certificate.")

    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(
        width / 2,
        20 * mm,
        "Keep this certificate with your PDF. It helps others verify the document by scanning the QR code.",
    )

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.getvalue()
