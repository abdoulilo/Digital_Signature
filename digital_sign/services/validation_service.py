from .hash_service import generate_file_hash
from .signature_service import verify_signature


STATUS_VALID    = "valid"      
STATUS_MODIFIED = "modified"   
STATUS_UNKNOWN  = "unknown"    

def validate_signed_document(
    file_path: str,
    stored_hash: str,
    signature: str,
    public_key: str,
) -> dict:
    """
    Validate an uploaded PDF against the stored certificate.

    """
    result = {
        "status":        STATUS_UNKNOWN,
        "uploaded_hash": None,
        "stored_hash":   stored_hash,
        "hashes_match":  False,
        "signature_ok":  False,
        "message":       "",
    }

    if not signature or not public_key:
        result["message"] = (
            "Certificate is incomplete — signature or public key is missing."
        )
        return result


    try:
        uploaded_hash = generate_file_hash(file_path)
    except Exception as exc:
        result["message"] = f"Could not read the uploaded file: {exc}"
        return result

    result["uploaded_hash"] = uploaded_hash


    sig_ok = verify_signature(
        file_hash=stored_hash,
        signature_base64=signature,
        public_key_pem=public_key,
    )
    result["signature_ok"] = sig_ok

    if not sig_ok:

        result["status"]  = STATUS_UNKNOWN
        result["message"] = (
            "Could not verify the certificate signature. "
            "The certificate may be tampered with or the wrong key was used."
        )
        return result

 
    hashes_match = uploaded_hash == stored_hash
    result["hashes_match"] = hashes_match

    if hashes_match:
        result["status"]  = STATUS_VALID
        result["message"] = (
            "Document is authentic. "
            "The file matches the signed certificate and has not been modified."
        )
    else:
        result["status"]  = STATUS_MODIFIED
        result["message"] = (
            "Document has been modified. "
            "The file content no longer matches the hash recorded at signing time."
        )

    return result
