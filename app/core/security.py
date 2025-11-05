"""
Password hashing and verification using pwdlib with Argon2id.

Argon2id is the recommended algorithm (PHC winner) for production use.
It provides resistance against GPU/side-channel attacks.
"""
from pwdlib import PasswordHash

# Initialize password hasher with Argon2id (recommended settings)
# This will automatically use Argon2id algorithm
pwd_context = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """
    Hash a plain password using Argon2id.
    
    Args:
        plain_password: The plain text password
        
    Returns:
        The Argon2id hash string
        
    Example:
        >>> hash_password("mySecurePass123")
        '$argon2id$v=19$m=65536,t=3,p=4$...'
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hash.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The stored Argon2id hash
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("myPass")
        >>> verify_password("myPass", hashed)
        True
        >>> verify_password("wrongPass", hashed)
        False
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Handle invalid hash format gracefully
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be updated.
    
    This is useful for upgrading old hashes when security
    parameters change or when migrating from another algorithm.
    
    Args:
        hashed_password: The stored hash
        
    Returns:
        True if the hash should be regenerated
    """
    try:
        return pwd_context.needs_rehash(hashed_password)
    except Exception:
        # If we can't parse the hash, it definitely needs rehashing
        return True
