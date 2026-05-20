import hashlib


def generate_file_hash(file_path):
    """
    Generate SHA-256 hash from a file.
    """
    sha256 = hashlib.sha256()

    with open(file_path, 'rb') as file:
        for block in iter(lambda: file.read(4096), b''):
            sha256.update(block)

    return sha256.hexdigest()