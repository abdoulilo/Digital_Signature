import io
import os

import fitz  
from django.conf import settings

from .qr_service import generate_qr_code


def is_valid_pdf(file_path: str) -> bool:
    try:
        with fitz.open(file_path) as pdf:
            return pdf.page_count > 0
    except Exception:
        return False



QR_SIZE        = 90  
QR_MARGIN      = 12   
BLOCK_PADDING  = 8    
LABEL_FONT_SZ  = 7
LABEL_TEXT     = "Scan to verify authenticity"


def embed_qr_block(document, certificate_url: str) -> str:
    """
    Stamps a small QR-code block
    
    """
    original_path = document.original_pdf.path

    signed_dir = os.path.join(settings.MEDIA_ROOT, "pdfs", "signed")
    os.makedirs(signed_dir, exist_ok=True)

    original_filename = os.path.basename(document.original_pdf.name)
    signed_filename   = f"signed_{document.id}_{original_filename}"
    signed_path       = os.path.join(signed_dir, signed_filename)


    qr_png = generate_qr_code(certificate_url)


    pdf       = fitz.open(original_path)
    last_page = pdf[-1]
    pw, ph    = last_page.rect.width, last_page.rect.height

    x1 = pw  - QR_MARGIN
    y1 = ph  - QR_MARGIN
    x0 = x1  - QR_SIZE
    y0 = y1  - QR_SIZE

    qr_rect = fitz.Rect(x0, y0, x1, y1)


    label_height = LABEL_FONT_SZ + BLOCK_PADDING * 2
    backing_rect = fitz.Rect(
        x0 - BLOCK_PADDING,
        y0 - label_height - BLOCK_PADDING,
        x1 + BLOCK_PADDING,
        y1 + BLOCK_PADDING,
    )
    last_page.draw_rect(backing_rect, color=(1, 1, 1), fill=(1, 1, 1))

    last_page.draw_rect(backing_rect, color=(0.7, 0.7, 0.7), width=0.5)


    last_page.insert_image(qr_rect, stream=qr_png)


    label_y = y0 - BLOCK_PADDING - 2
    last_page.insert_text(
        (x0 - BLOCK_PADDING + 2, label_y),
        LABEL_TEXT,
        fontsize=LABEL_FONT_SZ,
        fontname="helv",
        color=(0.3, 0.3, 0.3),
    )


    pdf.save(signed_path)
    pdf.close()

    return f"pdfs/signed/{signed_filename}"
