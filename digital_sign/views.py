from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.files.storage import default_storage
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import DigitalDocument
from .forms import UploadPDFForm, VerifyPDFForm
from .services.hash_service import generate_file_hash
from .services.key_service import generate_key_pair
from .services.signature_service import sign_hash
from .services.validation_service import validate_signed_document
from .services.pdf_service import is_valid_pdf, create_signed_pdf_copy


def upload_pdf_view(request):
    """
    Upload a PDF document.
    """
    if request.method == 'POST':
        form = UploadPDFForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)

            if request.user.is_authenticated:
                document.uploaded_by = request.user

            document.save()

            file_path = document.original_pdf.path

            if not is_valid_pdf(file_path):
                document.status = 'failed'
                document.verification_message = 'Invalid PDF file.'
                document.save()

                messages.error(request, 'The uploaded file is not a valid PDF.')
                return redirect('upload_pdf')

            document.file_hash = generate_file_hash(file_path)
            document.status = 'hashed'
            document.verification_message = 'Hash generated successfully.'
            document.save()

            return redirect('sign_pdf', document_id=document.id)

    else:
        form = UploadPDFForm()

    return render(request, 'digital_sign/upload_pdf.html', {
        'form': form
    })


def sign_pdf_view(request, document_id):
    """
    Generate keys and sign the uploaded PDF hash.
    """
    document = get_object_or_404(DigitalDocument, id=document_id)

    if not document.file_hash:
        document.file_hash = generate_file_hash(document.original_pdf.path)
        document.status = 'hashed'
        document.save()

    if request.method == 'POST':
        private_key, public_key = generate_key_pair()

        signature = sign_hash(
            file_hash=document.file_hash,
            private_key_pem=private_key
        )

        document.private_key = private_key
        document.public_key = public_key
        document.signature = signature
        document.status = 'signed'
        document.verification_message = 'Document signed successfully.'
        document.save()

        signed_pdf_path = create_signed_pdf_copy(document)
        document.signed_pdf = signed_pdf_path
        document.save()

        messages.success(request, 'PDF signed successfully.')

        return redirect('result', document_id=document.id)

    return render(request, 'digital_sign/sign_pdf.html', {
        'document': document
    })


def verify_pdf_view(request):
    """
    Upload a PDF and verify it using signature + public key.
    """
    result = None

    if request.method == 'POST':
        form = VerifyPDFForm(request.POST, request.FILES)

        if form.is_valid():
            pdf_file = form.cleaned_data['pdf_file']
            signature = form.cleaned_data['signature']
            public_key = form.cleaned_data['public_key']

            saved_path = default_storage.save(f'temp_verify/{pdf_file.name}', pdf_file)
            full_path = default_storage.path(saved_path)

            result = validate_signed_document(
                file_path=full_path,
                signature=signature,
                public_key=public_key
            )

            return render(request, 'digital_sign/result.html', {
                'verification_result': result
            })

    else:
        form = VerifyPDFForm()

    return render(request, 'digital_sign/verify_pdf.html', {
        'form': form,
        'result': result
    })


def result_view(request, document_id=None):
    """
    Show signing or verification result.
    """
    document = None

    if document_id:
        document = get_object_or_404(DigitalDocument, id=document_id)

    return render(request, 'digital_sign/result.html', {
        'document': document
    })


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('upload_pdf')
    else:
        form = UserCreationForm()

    return render(request, 'registration/signup.html', {
        'form': form
    })