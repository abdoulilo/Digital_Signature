import os
import tempfile

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core import signing
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import JsonResponse, Http404, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import DigitalDocument
from .forms import UploadPDFForm, VerifyPDFForm
from .services.hash_service import generate_file_hash
from .services.key_service import generate_key_pair
from .services.signature_service import sign_hash
from .services.validation_service import validate_signed_document
from .services.pdf_service import is_valid_pdf
from .services.qr_service import generate_qr_code
from .services.certificate_pdf_service import generate_certificate_pdf


SIGN_SALT = "digital-sign-sign-flow"
RESULT_SALT = "digital-sign-result-flow"
CERTIFICATE_SALT = "digital-sign-certificate-flow"


def make_token(document, purpose, salt):
    """
    Create a URL-safe signed token.
    """
    signed_value = signing.dumps(
        {
            "id": document.id,
            "purpose": purpose,
        },
        salt=salt,
    )

    return urlsafe_base64_encode(force_bytes(signed_value))


def get_document_from_token(token, purpose, salt):
    """
    Read a document from a secure token.
    """
    try:
        try:
            signed_value = force_str(urlsafe_base64_decode(token))
        except Exception:
            signed_value = token

        data = signing.loads(signed_value, salt=salt)
    except Exception:
        raise Http404("Invalid link.")

    if data.get("purpose") != purpose:
        raise Http404("Invalid link.")

    document_id = data.get("id")

    if not document_id:
        raise Http404("Invalid link.")

    return get_object_or_404(DigitalDocument, id=document_id)


def get_filename(document):
    if hasattr(document, "filename"):
        filename_attr = document.filename
        if callable(filename_attr):
            return filename_attr()
        return filename_attr

    return os.path.basename(document.original_pdf.name)


def copy_original_to_signed_pdf(document):
    """
    Keep the PDF unchanged.

    """
    if getattr(document, "signed_pdf", None) and document.signed_pdf:
        return

    document.original_pdf.open("rb")
    pdf_bytes = document.original_pdf.read()
    document.original_pdf.close()

    original_name = os.path.basename(document.original_pdf.name)

    document.signed_pdf.save(
        f"signed_{document.id}_{original_name}",
        ContentFile(pdf_bytes),
        save=False,
    )


def upload_pdf_view(request):
 
    if request.method == "POST":
        form = UploadPDFForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)

            if request.user.is_authenticated:
                document.uploaded_by = request.user

            document.save()

            file_path = document.original_pdf.path

            if not is_valid_pdf(file_path):
                document.status = "failed"
                document.verification_message = "Invalid PDF file."
                document.save()

                messages.error(request, "The uploaded file is not a valid PDF.")
                return redirect("upload_pdf")

            document.file_hash = generate_file_hash(file_path)
            document.status = "hashed"
            document.verification_message = "Hash generated successfully."
            document.save()

            sign_token = make_token(document, "sign", SIGN_SALT)
            return redirect("sign_pdf", token=sign_token)

    else:
        form = UploadPDFForm()

    return render(request, "digital_sign/upload_pdf.html", {"form": form})


def sign_pdf_view(request, token):

    document = get_document_from_token(token, "sign", SIGN_SALT)

    if document.status == "signed":
        result_token = make_token(document, "result", RESULT_SALT)
        return redirect("result", token=result_token)

    if not document.file_hash:
        document.file_hash = generate_file_hash(document.original_pdf.path)
        document.status = "hashed"
        document.save()

    if request.method == "POST":
        private_key, public_key = generate_key_pair()

        signature = sign_hash(
            file_hash=document.file_hash,
            private_key_pem=private_key,
        )

        document.public_key = public_key
        document.signature = signature
        document.status = "signed"
        document.signed_at = timezone.now()
        document.verification_message = "Document signed successfully."

        copy_original_to_signed_pdf(document)

        document.save()

        messages.success(request, "PDF signed successfully.")

        result_token = make_token(document, "result", RESULT_SALT)
        return redirect("result", token=result_token)

    sign_url = reverse("sign_pdf", kwargs={"token": token})

    return render(
        request,
        "digital_sign/sign_pdf.html",
        {
            "document": document,
            "token": token,
            "sign_url": sign_url,
        },
    )


def result_view(request, token):
 
    document = get_document_from_token(token, "result", RESULT_SALT)

    if document.status != "signed" or not document.signed_at:
        raise Http404("Result not found.")

    certificate_token = make_token(document, "certificate", CERTIFICATE_SALT)

    certificate_url = request.build_absolute_uri(
        reverse("certificate_page", kwargs={"token": certificate_token})
    )

    certificate_pdf_url = reverse(
        "download_certificate_pdf",
        kwargs={"token": certificate_token},
    )

    return render(
        request,
        "digital_sign/result.html",
        {
            "document": document,
            "certificate_url": certificate_url,
            "certificate_pdf_url": certificate_pdf_url,
            "certificate_token": certificate_token,
        },
    )


def verify_pdf_view(request):

    result = None

    if request.method == "POST":
        form = VerifyPDFForm(request.POST, request.FILES)

        if form.is_valid():
            pdf_file = form.cleaned_data["pdf_file"]
            signature = form.cleaned_data["signature"]
            public_key = form.cleaned_data["public_key"]

            saved_path = default_storage.save(f"temp_verify/{pdf_file.name}", pdf_file)
            full_path = default_storage.path(saved_path)

            try:
                fresh_hash = generate_file_hash(full_path)

                result = validate_signed_document(
                    file_path=full_path,
                    stored_hash=fresh_hash,
                    signature=signature,
                    public_key=public_key,
                )
            finally:
                try:
                    default_storage.delete(saved_path)
                except Exception:
                    pass

            return render(request, "digital_sign/result.html", {"verification_result": result})

    else:
        form = VerifyPDFForm()

    return render(request, "digital_sign/verify_pdf.html", {"form": form, "result": result})


def certificate_page(request, token):

    document = get_document_from_token(token, "certificate", CERTIFICATE_SALT)

    if document.status != "signed" or not document.signed_at:
        raise Http404("Certificate not found.")

    upload_verify_url = request.build_absolute_uri(
        reverse("qr_verify_upload", kwargs={"token": token})
    )

    certificate_pdf_url = reverse(
        "download_certificate_pdf",
        kwargs={"token": token},
    )

    return render(
        request,
        "digital_sign/certificate_page.html",
        {
            "document": document,
            "verify_url": upload_verify_url,
            "certificate_pdf_url": certificate_pdf_url,
        },
    )


@csrf_exempt
@require_http_methods(["POST"])
def qr_verify_upload(request, token):

    document = get_document_from_token(token, "certificate", CERTIFICATE_SALT)

    if document.status != "signed" or not document.signed_at:
        return JsonResponse(
            {
                "status": "error",
                "message": "Certificate not found.",
            },
            status=404,
        )

    uploaded_file = request.FILES.get("pdf")

    if not uploaded_file:
        return JsonResponse(
            {
                "status": "error",
                "message": "No PDF uploaded. Send the file using field name 'pdf'.",
            },
            status=400,
        )

    if not uploaded_file.name.lower().endswith(".pdf"):
        return JsonResponse(
            {
                "status": "error",
                "message": "Only PDF files are accepted.",
            },
            status=400,
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        for chunk in uploaded_file.chunks():
            tmp.write(chunk)

        tmp_path = tmp.name

    try:
        result = validate_signed_document(
            file_path=tmp_path,
            stored_hash=document.file_hash,
            signature=document.signature,
            public_key=document.public_key,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    result["document"] = {
        "document_id": f"DS-{document.id:06d}",
        "filename": get_filename(document),
        "signed_at": document.signed_at.isoformat() if document.signed_at else None,
        "status": document.status,
    }

    return JsonResponse(result)


def download_certificate_pdf(request, token):

    document = get_document_from_token(token, "certificate", CERTIFICATE_SALT)

    if document.status != "signed" or not document.signed_at:
        raise Http404("Certificate not found.")

    certificate_url = request.build_absolute_uri(
        reverse("certificate_page", kwargs={"token": token})
    )

    qr_png = generate_qr_code(certificate_url)

    pdf_bytes = generate_certificate_pdf(
        certificate=document,
        verify_url=certificate_url,
        qr_png=qr_png,
    )

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="DS-{document.id:06d}-certificate.pdf"'
    )

    return response


def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("upload_pdf")
    else:
        form = UserCreationForm()

    return render(request, "registration/signup.html", {"form": form})
