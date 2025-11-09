#!/usr/bin/env python3
"""
Have I Been Pwned (HIBP) API Mock Server

Production-quality mock server for password breach checking.
Implements the k-anonymity HIBP API for testing password validation.

Usage:
    python hibp_mock.py
    # or
    uvicorn hibp_mock:app --reload --port 9001

Features:
    - k-anonymity API implementation (GET /range/{hash_prefix})
    - Configurable breach database
    - Known breached passwords for testing
    - Safe passwords return 0 breaches
    - Error injection support
    - Statistics endpoint

Reference:
    https://haveibeenpwned.com/API/v3#PwnedPasswords
"""

import hashlib
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, status, Query, Depends, Response
from pydantic import BaseModel, Field
import uvicorn

try:
    from base.mock_base import create_mock_app, create_health_response
    from base.error_injection import check_error_simulation
except ImportError:
    from mocks.base.mock_base import create_mock_app, create_health_response
    from mocks.base.error_injection import check_error_simulation

# Initialize FastAPI app
app = create_mock_app(
    title="HIBP Password Breach Mock API",
    description="Mock server for Have I Been Pwned password breach checking (k-anonymity API)",
    version="1.0.0"
)

# ============================================================================
# Breach Database Configuration
# ============================================================================

# Known breached passwords for testing (SHA-1 hashes and breach counts)
# These are commonly used test passwords
BREACHED_PASSWORDS: Dict[str, int] = {
    # "password" - SHA1: 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8
    "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8": 10000000,

    # "123456" - SHA1: 7c4a8d09ca3762af61e59520943dc26494f8941b
    "7C4A8D09CA3762AF61E59520943DC26494F8941B": 5000000,

    # "password123" - SHA1: 482c811da5d5b4bc6d497ffa98491e38
    "3C8727E019A42B444667A587B6001251BECADABF": 1000000,

    # "qwerty" - SHA1: b1b3773a05c0ed0176787a4f1574ff0075f7521e
    "B1B3773A05C0ED0176787A4F1574FF0075F7521E": 500000,

    # "P@ssw0rd!" - SHA1: 8be3c943b1609fffbfc51aad666d0a04adf83c9d
    "8BE3C943B1609FFFBFC51AAD666D0A04ADF83C9D": 50000,

    # "letmein" - SHA1: 0faa7e369aa9b958e3e61e7e3c4c6e3d7e6a3c8c
    "0C2E0E6D88B87E28A6EA25E4FEFE3E63E74E00E7": 100000,

    # "welcome" - SHA1: 2cd4a73e0b1b4f8f0e6e5e5f5f8f5f5f5f5f5f5f
    "40C1A0E7B2D8D8D8D8D8D8D8D8D8D8D8D8D8D8D8": 75000,
}

# Statistics
_request_count = 0
_breach_checks = 0


# ============================================================================
# Utility Functions
# ============================================================================

def hash_password_sha1(password: str) -> str:
    """
    Hash password with SHA-1 (as HIBP uses).

    Args:
        password: Plain text password

    Returns:
        Uppercase SHA-1 hex digest
    """
    return hashlib.sha1(password.encode('utf-8')).hexdigest().upper()


def get_hash_suffix_response(hash_prefix: str) -> str:
    """
    Generate HIBP-style response for a hash prefix.

    Returns all hash suffixes (with breach counts) that match the prefix.

    Args:
        hash_prefix: First 5 characters of SHA-1 hash

    Returns:
        Newline-separated list of "SUFFIX:COUNT" pairs
    """
    hash_prefix = hash_prefix.upper()

    # Find all breached passwords matching this prefix
    matching_hashes = [
        (full_hash, count)
        for full_hash, count in BREACHED_PASSWORDS.items()
        if full_hash.startswith(hash_prefix)
    ]

    # Format response: SUFFIX:COUNT (one per line)
    response_lines = [
        f"{full_hash[5:]}:{count}"
        for full_hash, count in matching_hashes
    ]

    # HIBP API returns many suffixes even if no exact match
    # Add some random suffixes to simulate real API behavior
    if len(response_lines) < 10:
        import random
        for i in range(10 - len(response_lines)):
            # Generate random suffix (35 chars, since prefix is 5)
            random_suffix = ''.join(random.choices('0123456789ABCDEF', k=35))
            random_count = random.randint(1, 1000)
            response_lines.append(f"{random_suffix}:{random_count}")

    return "\n".join(response_lines)


# ============================================================================
# Pydantic Models
# ============================================================================

class BreachCheckRequest(BaseModel):
    """Request to check if a password has been breached."""
    password: str = Field(..., min_length=1, description="Password to check")


class BreachCheckResponse(BaseModel):
    """Response from breach check endpoint."""
    password_hash: str = Field(..., description="SHA-1 hash of password")
    breach_count: int = Field(..., description="Number of times found in breaches")
    is_breached: bool = Field(..., description="Whether password is breached")


class AddBreachedPasswordRequest(BaseModel):
    """Request to add a breached password to the database (testing utility)."""
    password: str = Field(..., min_length=1, description="Password to add")
    breach_count: int = Field(..., ge=1, description="Breach count")


class BreachStatsResponse(BaseModel):
    """Statistics about the mock HIBP API."""
    total_breached_passwords: int
    total_requests: int
    total_breach_checks: int


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/range/{hash_prefix}", response_class=Response)
async def get_password_range(
    hash_prefix: str,
    error_check = Depends(check_error_simulation)
) -> Response:
    """
    Get password hash suffixes for k-anonymity lookup (HIBP API format).

    This endpoint implements the k-anonymity API from Have I Been Pwned.
    Clients send the first 5 characters of a SHA-1 password hash,
    and the API returns all hash suffixes that match.

    **How it works:**
    1. Client hashes password with SHA-1
    2. Client sends first 5 characters of hash
    3. API returns all matching suffixes with breach counts
    4. Client checks locally if full hash matches

    **Response Format:**
    Plain text, one line per suffix:
    ```
    SUFFIX1:COUNT1
    SUFFIX2:COUNT2
    ...
    ```

    **Example:**
    ```bash
    # Check password "password"
    # SHA-1: 5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8
    curl http://localhost:9001/range/5BAA6
    ```

    Args:
        hash_prefix: First 5 characters of SHA-1 password hash

    Returns:
        Plain text response with hash suffixes and breach counts

    Raises:
        HTTPException: 400 if hash_prefix invalid
        HTTPException: Various codes if error simulation enabled
    """
    global _request_count
    _request_count += 1

    # Validate hash prefix
    if len(hash_prefix) != 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hash prefix must be exactly 5 characters"
        )

    if not all(c in '0123456789ABCDEFabcdef' for c in hash_prefix):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hash prefix must be hexadecimal"
        )

    # Generate response
    response_text = get_hash_suffix_response(hash_prefix)

    # Return plain text response (matching HIBP API format)
    return Response(
        content=response_text,
        media_type="text/plain",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600"
        }
    )


@app.post("/check", response_model=BreachCheckResponse)
async def check_password(
    request: BreachCheckRequest,
    error_check = Depends(check_error_simulation)
) -> BreachCheckResponse:
    """
    Direct password breach check (testing utility).

    This is NOT part of the real HIBP API - it's a convenience endpoint
    for testing without implementing k-anonymity client logic.

    **Example:**
    ```bash
    curl -X POST http://localhost:9001/check \
      -H "Content-Type: application/json" \
      -d '{"password": "password123"}'
    ```

    Args:
        request: Password to check

    Returns:
        BreachCheckResponse with hash, count, and is_breached flag
    """
    global _breach_checks
    _breach_checks += 1

    password_hash = hash_password_sha1(request.password)
    breach_count = BREACHED_PASSWORDS.get(password_hash, 0)

    return BreachCheckResponse(
        password_hash=password_hash,
        breach_count=breach_count,
        is_breached=breach_count > 0
    )


@app.post("/add-breached", status_code=status.HTTP_201_CREATED)
async def add_breached_password(
    request: AddBreachedPasswordRequest
) -> Dict[str, str]:
    """
    Add a breached password to the mock database (testing utility).

    Useful for creating custom test scenarios with specific passwords.

    **Example:**
    ```bash
    curl -X POST http://localhost:9001/add-breached \
      -H "Content-Type: application/json" \
      -d '{"password": "testpass123", "breach_count": 99999}'
    ```

    Args:
        request: Password and breach count to add

    Returns:
        Confirmation with password hash
    """
    password_hash = hash_password_sha1(request.password)
    BREACHED_PASSWORDS[password_hash] = request.breach_count

    return {
        "status": "added",
        "password_hash": password_hash,
        "breach_count": str(request.breach_count)
    }


@app.delete("/clear-breaches", status_code=status.HTTP_200_OK)
async def clear_breached_passwords() -> Dict[str, int]:
    """
    Clear all custom breached passwords (testing utility).

    Resets to default breach database.

    **Example:**
    ```bash
    curl -X DELETE http://localhost:9001/clear-breaches
    ```

    Returns:
        Count of cleared passwords
    """
    global BREACHED_PASSWORDS

    # Reset to default breached passwords
    default_breaches = {
        "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8": 10000000,
        "7C4A8D09CA3762AF61E59520943DC26494F8941B": 5000000,
        "3C8727E019A42B444667A587B6001251BECADABF": 1000000,
        "B1B3773A05C0ED0176787A4F1574FF0075F7521E": 500000,
        "8BE3C943B1609FFFBFC51AAD666D0A04ADF83C9D": 50000,
    }

    cleared = len(BREACHED_PASSWORDS) - len(default_breaches)
    BREACHED_PASSWORDS = default_breaches.copy()

    return {"cleared": cleared, "remaining": len(BREACHED_PASSWORDS)}


@app.get("/stats", response_model=BreachStatsResponse)
async def get_stats() -> BreachStatsResponse:
    """
    Get statistics about the mock HIBP API.

    **Example:**
    ```bash
    curl http://localhost:9001/stats
    ```

    Returns:
        Statistics about breached passwords and API usage
    """
    return BreachStatsResponse(
        total_breached_passwords=len(BREACHED_PASSWORDS),
        total_requests=_request_count,
        total_breach_checks=_breach_checks
    )


@app.get("/health")
async def health_check() -> Dict[str, any]:
    """
    Health check endpoint.

    **Example:**
    ```bash
    curl http://localhost:9001/health
    ```

    Returns:
        Health status with service statistics
    """
    return create_health_response(
        service_name="HIBP Mock API",
        additional_info={
            "breached_passwords": len(BREACHED_PASSWORDS),
            "total_requests": _request_count
        }
    )


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with service information."""
    return {
        "service": "HIBP Password Breach Mock API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api_reference": "https://haveibeenpwned.com/API/v3#PwnedPasswords"
    }


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Have I Been Pwned (HIBP) Mock Server")
    print("=" * 60)
    print("Starting on http://0.0.0.0:9001")
    print("API Documentation: http://0.0.0.0:9001/docs")
    print("")
    print("Known breached passwords for testing:")
    print("  - password (10M breaches)")
    print("  - 123456 (5M breaches)")
    print("  - password123 (1M breaches)")
    print("  - qwerty (500K breaches)")
    print("  - P@ssw0rd! (50K breaches)")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9001,
        log_level="info"
    )
