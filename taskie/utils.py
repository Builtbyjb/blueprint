import secrets

def generate_crypto_string(length=32):
    """Generates a unique URL-safe cryptographic string of the specified length.

    Args:
        length (int): Desired length of the output string. Defaults to 32.

    Returns:
        str: A cryptographically secure random string.
    """
    required_bytes = (length * 6 + 7) // 8  # Calculate bytes needed for the desired length
    token = secrets.token_urlsafe(required_bytes)
    return token[:length]
