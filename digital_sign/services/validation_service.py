from .hash_service import generate_file_hash
from .signature_service import verify_signature


def validate_signed_document(file_path, signature, public_key):
    """
    Validate uploaded PDF against signature and public key.
    """
    file_hash = generate_file_hash(file_path)

    is_valid = verify_signature(
        file_hash=file_hash,
        signature_base64=signature,
        public_key_pem=public_key
    )

    return {
        'file_hash': file_hash,
        'is_valid': is_valid,
        'message': 'Document signature is valid.' if is_valid else 'Document signature is invalid or the file was changed.'
    }