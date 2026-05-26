import io
import qrcode
from qrcode.image.pure import PyPNGImage


def generate_qr_code(certificate_url: str) -> bytes:
    """
    Generate a QR code PNG (as bytes) that links to the certificate page.

    """
    qr = qrcode.QRCode(
        version=None,          
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=6,
        border=2,
    )
    qr.add_data(certificate_url)
    qr.make(fit=True)

    img = qr.make_image(image_factory=PyPNGImage)

    buffer = io.BytesIO()
    img.save(buffer)
    return buffer.getvalue()
