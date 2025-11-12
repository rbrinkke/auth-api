"""
PKCE (Proof Key for Code Exchange) Utilities

RFC 7636: PKCE for OAuth 2.0
https://datatracker.ietf.org/doc/html/rfc7636

PKCE prevents authorization code interception attacks by binding
the authorization request to the token request using cryptographic proof.
"""

import secrets
import hashlib
import base64
from app.core.logging_config import get_logger

logger = get_logger(__name__)


def generate_code_verifier(length: int = 64) -> str:
    """
    Generate cryptographically random code_verifier.

    Per RFC 7636:
    - code_verifier = high-entropy cryptographic random STRING
    - Length: 43-128 characters
    - Character set: [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"

    Args:
        length: Length of verifier (43-128, default 64)

    Returns:
        Base64url-encoded random string (URL-safe, no padding)

    Example:
        >>> verifier = generate_code_verifier()
        >>> len(verifier)
        86  # Base64url encoding increases length
    """
    if not (43 <= length <= 128):
        raise ValueError("code_verifier length must be between 43 and 128")

    # Generate random bytes (256 bits of entropy for default length 64)
    random_bytes = secrets.token_bytes(length)

    # Base64url encode (URL-safe, remove padding)
    code_verifier = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')

    logger.debug("pkce_code_verifier_generated", length=len(code_verifier))

    return code_verifier


def generate_code_challenge(code_verifier: str, method: str = "S256") -> str:
    """
    Generate code_challenge from code_verifier.

    Per RFC 7636:
    - S256: code_challenge = BASE64URL(SHA256(ASCII(code_verifier)))
    - plain: code_challenge = code_verifier (not recommended)

    Args:
        code_verifier: Random string from generate_code_verifier()
        method: Challenge method ("S256" or "plain", default "S256")

    Returns:
        Base64url-encoded challenge string

    Raises:
        ValueError: If method is invalid or code_verifier is invalid

    Example:
        >>> verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        >>> challenge = generate_code_challenge(verifier)
        >>> challenge
        'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM'
    """
    if not code_verifier:
        raise ValueError("code_verifier cannot be empty")

    if len(code_verifier) < 43 or len(code_verifier) > 128:
        raise ValueError("code_verifier length must be between 43 and 128")

    if method == "S256":
        # SHA256 hash
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        # Base64url encode (URL-safe, remove padding)
        code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

        logger.debug("pkce_code_challenge_generated",
                    method="S256",
                    challenge_length=len(code_challenge))

        return code_challenge

    elif method == "plain":
        # Plain text (not recommended, only for debugging)
        logger.warning("pkce_plain_method_used",
                      message="Using plain PKCE method (not recommended for production)")
        return code_verifier

    else:
        raise ValueError(f"Invalid code_challenge_method: {method} (must be 'S256' or 'plain')")


def validate_pkce(
    stored_challenge: str,
    received_verifier: str,
    method: str = "S256"
) -> bool:
    """
    Validate PKCE challenge against verifier.

    This is the core PKCE validation function. It prevents authorization
    code interception attacks by ensuring the client that requests the
    token is the same client that initiated the authorization request.

    Args:
        stored_challenge: code_challenge from authorization request (stored in DB)
        received_verifier: code_verifier from token request
        method: Challenge method used ("S256" or "plain")

    Returns:
        True if validation succeeds, False otherwise

    Security:
        - Uses constant-time comparison to prevent timing attacks
        - Validates both challenge and verifier format
        - Logs all validation attempts for security monitoring

    Example:
        >>> challenge = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
        >>> verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        >>> validate_pkce(challenge, verifier, "S256")
        True
    """
    if not stored_challenge or not received_verifier:
        logger.warning("pkce_validation_failed",
                      reason="empty_challenge_or_verifier")
        return False

    try:
        # Generate challenge from received verifier
        computed_challenge = generate_code_challenge(received_verifier, method)

        # Constant-time comparison (prevents timing attacks)
        is_valid = secrets.compare_digest(stored_challenge, computed_challenge)

        if is_valid:
            logger.info("pkce_validation_success", method=method)
        else:
            logger.warning("pkce_validation_failed",
                          reason="challenge_mismatch",
                          method=method)

        return is_valid

    except Exception as e:
        logger.error("pkce_validation_error",
                    error=str(e),
                    method=method,
                    exc_info=True)
        return False


def generate_authorization_code() -> str:
    """
    Generate cryptographically random authorization code.

    Per RFC 6749:
    - MUST be short-lived (recommend 10 minutes maximum)
    - MUST be single-use
    - MUST be unpredictable (high entropy)

    Returns:
        Base64url-encoded random string (256 bits of entropy)

    Example:
        >>> code = generate_authorization_code()
        >>> len(code)
        43  # Base64url encoding of 32 bytes
    """
    # 32 bytes = 256 bits of entropy
    random_bytes = secrets.token_bytes(32)

    # Base64url encode (URL-safe, remove padding)
    code = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')

    logger.debug("authorization_code_generated", length=len(code))

    return code


def generate_state() -> str:
    """
    Generate cryptographically random state parameter for CSRF protection.

    The state parameter is used to protect against CSRF attacks by binding
    the authorization request to the client's session.

    Returns:
        Base64url-encoded random string (256 bits of entropy)

    Example:
        >>> state = generate_state()
        >>> len(state)
        43
    """
    # 32 bytes = 256 bits of entropy
    random_bytes = secrets.token_bytes(32)

    # Base64url encode
    state = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')

    logger.debug("state_generated", length=len(state))

    return state


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_code_verifier_format(code_verifier: str) -> bool:
    """
    Validate code_verifier format per RFC 7636.

    Checks:
    - Length: 43-128 characters
    - Character set: [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"

    Args:
        code_verifier: Code verifier to validate

    Returns:
        True if valid format, False otherwise
    """
    if not code_verifier:
        return False

    if not (43 <= len(code_verifier) <= 128):
        logger.warning("pkce_invalid_verifier_length",
                      length=len(code_verifier))
        return False

    # Valid character set
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")

    if not all(c in allowed_chars for c in code_verifier):
        logger.warning("pkce_invalid_verifier_characters")
        return False

    return True


def validate_code_challenge_format(code_challenge: str, method: str) -> bool:
    """
    Validate code_challenge format.

    Args:
        code_challenge: Code challenge to validate
        method: Challenge method ("S256" or "plain")

    Returns:
        True if valid format, False otherwise
    """
    if not code_challenge:
        return False

    if method == "S256":
        # SHA256 base64url is always 43 characters (without padding)
        if len(code_challenge) != 43:
            logger.warning("pkce_invalid_challenge_length",
                          length=len(code_challenge),
                          expected=43)
            return False

        # Base64url character set
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")

        if not all(c in allowed_chars for c in code_challenge):
            logger.warning("pkce_invalid_challenge_characters")
            return False

    elif method == "plain":
        # Plain method: challenge = verifier
        return validate_code_verifier_format(code_challenge)

    else:
        logger.warning("pkce_invalid_method", method=method)
        return False

    return True
