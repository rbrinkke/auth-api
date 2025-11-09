#!/usr/bin/env python3
"""
Redis Mock Server with TTL Simulation

Production-quality mock server for Redis operations with automatic TTL expiration.
Provides HTTP API that mimics Redis commands with TTL tracking and cleanup.

Usage:
    python redis_mock.py
    # or
    uvicorn redis_mock:app --reload --port 9002

Features:
    - Full Redis-like operations (get, set, setex, delete, exists, ttl)
    - Automatic TTL expiration with background cleanup
    - Key pattern matching for queries
    - Statistics and introspection endpoints
    - Test isolation via clear endpoint
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from fastapi import FastAPI, HTTPException, status, Query, Depends, BackgroundTasks
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
    title="Redis Mock Server",
    description="Mock Redis server with TTL simulation for testing",
    version="1.0.0"
)

# ============================================================================
# In-Memory Storage
# ============================================================================

@dataclass
class StoredValue:
    """Value stored in mock Redis with TTL tracking."""
    value: str
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None

    def is_expired(self) -> bool:
        """Check if value has expired."""
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at

    def ttl_seconds(self) -> int:
        """Get remaining TTL in seconds (-1 if no expiry, -2 if expired)."""
        if self.expires_at is None:
            return -1
        if self.is_expired():
            return -2
        return int(self.expires_at - time.time())


# Global in-memory storage
_storage: Dict[str, StoredValue] = {}
_stats = {
    "get_count": 0,
    "set_count": 0,
    "delete_count": 0,
    "expired_count": 0
}


def cleanup_expired_keys():
    """Remove expired keys from storage."""
    global _storage, _stats

    expired_keys = [
        key for key, value in _storage.items()
        if value.is_expired()
    ]

    for key in expired_keys:
        del _storage[key]
        _stats["expired_count"] += 1


async def background_ttl_cleanup():
    """Background task for periodic TTL cleanup."""
    while True:
        await asyncio.sleep(5)  # Run every 5 seconds
        cleanup_expired_keys()


# ============================================================================
# Pydantic Models
# ============================================================================

class SetRequest(BaseModel):
    """Request to set a key-value pair."""
    key: str = Field(..., min_length=1, description="Redis key")
    value: str = Field(..., description="Value to store")
    ex: Optional[int] = Field(None, ge=1, description="Expiration in seconds")


class SetexRequest(BaseModel):
    """Request to set a key-value pair with expiration."""
    key: str = Field(..., min_length=1, description="Redis key")
    seconds: int = Field(..., ge=1, description="TTL in seconds")
    value: str = Field(..., description="Value to store")


class GetResponse(BaseModel):
    """Response from GET operation."""
    key: str
    value: Optional[str]
    exists: bool
    ttl: Optional[int] = Field(None, description="Remaining TTL in seconds (-1 if no expiry)")


class KeysResponse(BaseModel):
    """Response from KEYS operation."""
    pattern: str
    keys: List[str]
    total: int


class StatsResponse(BaseModel):
    """Statistics about the mock Redis server."""
    total_keys: int
    get_count: int
    set_count: int
    delete_count: int
    expired_count: int


class KeyInfoResponse(BaseModel):
    """Detailed information about a key."""
    key: str
    exists: bool
    value: Optional[str] = None
    ttl: Optional[int] = None
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


# ============================================================================
# Redis Operations
# ============================================================================

@app.post("/set", status_code=status.HTTP_200_OK)
async def redis_set(
    request: SetRequest,
    error_check = Depends(check_error_simulation)
) -> Dict[str, str]:
    """
    SET operation - Set key to value with optional expiration.

    **Example:**
    ```bash
    # Set without expiration
    curl -X POST http://localhost:9002/set \
      -H "Content-Type: application/json" \
      -d '{"key": "user:123", "value": "john@example.com"}'

    # Set with expiration
    curl -X POST http://localhost:9002/set \
      -H "Content-Type: application/json" \
      -d '{"key": "session:abc", "value": "user_data", "ex": 3600}'
    ```

    Args:
        request: Key, value, and optional expiration

    Returns:
        Success confirmation
    """
    global _storage, _stats

    expires_at = None
    if request.ex is not None:
        expires_at = time.time() + request.ex

    _storage[request.key] = StoredValue(
        value=request.value,
        expires_at=expires_at
    )
    _stats["set_count"] += 1

    return {"status": "OK", "key": request.key}


@app.post("/setex", status_code=status.HTTP_200_OK)
async def redis_setex(
    request: SetexRequest,
    error_check = Depends(check_error_simulation)
) -> Dict[str, str]:
    """
    SETEX operation - Set key to value with expiration in seconds.

    **Example:**
    ```bash
    curl -X POST http://localhost:9002/setex \
      -H "Content-Type: application/json" \
      -d '{"key": "verify_token:abc123", "seconds": 600, "value": "user_id:123"}'
    ```

    Args:
        request: Key, value, and expiration time

    Returns:
        Success confirmation
    """
    global _storage, _stats

    expires_at = time.time() + request.seconds

    _storage[request.key] = StoredValue(
        value=request.value,
        expires_at=expires_at
    )
    _stats["set_count"] += 1

    return {"status": "OK", "key": request.key}


@app.get("/get/{key}", response_model=GetResponse)
async def redis_get(
    key: str,
    error_check = Depends(check_error_simulation)
) -> GetResponse:
    """
    GET operation - Get value of key.

    Returns None if key doesn't exist or has expired.

    **Example:**
    ```bash
    curl http://localhost:9002/get/user:123
    ```

    Args:
        key: Redis key to retrieve

    Returns:
        GetResponse with value and metadata
    """
    global _stats
    _stats["get_count"] += 1

    # Cleanup expired keys first
    cleanup_expired_keys()

    stored = _storage.get(key)

    if stored is None or stored.is_expired():
        return GetResponse(
            key=key,
            value=None,
            exists=False,
            ttl=None
        )

    return GetResponse(
        key=key,
        value=stored.value,
        exists=True,
        ttl=stored.ttl_seconds() if stored.expires_at else -1
    )


@app.delete("/delete/{key}", status_code=status.HTTP_200_OK)
async def redis_delete(
    key: str,
    error_check = Depends(check_error_simulation)
) -> Dict[str, Any]:
    """
    DELETE operation - Delete a key.

    **Example:**
    ```bash
    curl -X DELETE http://localhost:9002/delete/user:123
    ```

    Args:
        key: Redis key to delete

    Returns:
        Deletion status (1 if deleted, 0 if key didn't exist)
    """
    global _storage, _stats

    if key in _storage:
        del _storage[key]
        _stats["delete_count"] += 1
        return {"deleted": 1, "key": key}

    return {"deleted": 0, "key": key}


@app.get("/exists/{key}")
async def redis_exists(
    key: str,
    error_check = Depends(check_error_simulation)
) -> Dict[str, Any]:
    """
    EXISTS operation - Check if key exists.

    **Example:**
    ```bash
    curl http://localhost:9002/exists/user:123
    ```

    Args:
        key: Redis key to check

    Returns:
        Existence status (1 if exists, 0 if not)
    """
    cleanup_expired_keys()

    stored = _storage.get(key)
    exists = stored is not None and not stored.is_expired()

    return {"exists": 1 if exists else 0, "key": key}


@app.get("/ttl/{key}")
async def redis_ttl(
    key: str,
    error_check = Depends(check_error_simulation)
) -> Dict[str, Any]:
    """
    TTL operation - Get remaining time to live in seconds.

    Returns:
        - Positive number: seconds until expiration
        - -1: key exists but has no expiration
        - -2: key doesn't exist or has expired

    **Example:**
    ```bash
    curl http://localhost:9002/ttl/session:abc
    ```

    Args:
        key: Redis key to check

    Returns:
        TTL in seconds
    """
    cleanup_expired_keys()

    stored = _storage.get(key)

    if stored is None or stored.is_expired():
        return {"ttl": -2, "key": key}

    return {"ttl": stored.ttl_seconds(), "key": key}


@app.get("/keys", response_model=KeysResponse)
async def redis_keys(
    pattern: str = Query("*", description="Key pattern (* for wildcard)")
) -> KeysResponse:
    """
    KEYS operation - Find all keys matching pattern.

    **Pattern Matching:**
    - `*` matches any characters (e.g., `user:*`)
    - `?` matches single character
    - Simple prefix/suffix matching

    **Example:**
    ```bash
    # Get all keys
    curl http://localhost:9002/keys

    # Get keys with pattern
    curl http://localhost:9002/keys?pattern=verify_token:*
    ```

    Args:
        pattern: Key pattern to match

    Returns:
        List of matching keys
    """
    cleanup_expired_keys()

    all_keys = list(_storage.keys())

    if pattern == "*":
        matched_keys = all_keys
    else:
        # Simple pattern matching (supports prefix* and *suffix and *middle*)
        import re
        regex_pattern = pattern.replace("*", ".*").replace("?", ".")
        regex = re.compile(f"^{regex_pattern}$")
        matched_keys = [key for key in all_keys if regex.match(key)]

    return KeysResponse(
        pattern=pattern,
        keys=matched_keys,
        total=len(matched_keys)
    )


@app.get("/info/{key}", response_model=KeyInfoResponse)
async def redis_info(
    key: str
) -> KeyInfoResponse:
    """
    Get detailed information about a key (testing utility).

    **Example:**
    ```bash
    curl http://localhost:9002/info/user:123
    ```

    Args:
        key: Redis key to inspect

    Returns:
        Detailed key information
    """
    cleanup_expired_keys()

    stored = _storage.get(key)

    if stored is None or stored.is_expired():
        return KeyInfoResponse(
            key=key,
            exists=False
        )

    return KeyInfoResponse(
        key=key,
        exists=True,
        value=stored.value,
        ttl=stored.ttl_seconds(),
        created_at=datetime.fromtimestamp(stored.created_at).isoformat() + "Z",
        expires_at=datetime.fromtimestamp(stored.expires_at).isoformat() + "Z" if stored.expires_at else None
    )


@app.post("/clear", status_code=status.HTTP_200_OK)
async def clear_all() -> Dict[str, Any]:
    """
    Clear all keys (test isolation utility).

    **Example:**
    ```bash
    curl -X POST http://localhost:9002/clear
    ```

    Returns:
        Count of cleared keys
    """
    global _storage, _stats

    cleared_count = len(_storage)
    _storage.clear()

    return {
        "status": "cleared",
        "keys_cleared": cleared_count,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """
    Get statistics about the mock Redis server.

    **Example:**
    ```bash
    curl http://localhost:9002/stats
    ```

    Returns:
        Statistics about operations and keys
    """
    cleanup_expired_keys()

    return StatsResponse(
        total_keys=len(_storage),
        get_count=_stats["get_count"],
        set_count=_stats["set_count"],
        delete_count=_stats["delete_count"],
        expired_count=_stats["expired_count"]
    )


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    **Example:**
    ```bash
    curl http://localhost:9002/health
    ```

    Returns:
        Health status with key count
    """
    cleanup_expired_keys()

    return create_health_response(
        service_name="Redis Mock",
        additional_info={
            "total_keys": len(_storage),
            "total_operations": sum([
                _stats["get_count"],
                _stats["set_count"],
                _stats["delete_count"]
            ])
        }
    )


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with service information."""
    return {
        "service": "Redis Mock Server",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Start background TTL cleanup task."""
    asyncio.create_task(background_ttl_cleanup())


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Redis Mock Server with TTL Simulation")
    print("=" * 60)
    print("Starting on http://0.0.0.0:9002")
    print("API Documentation: http://0.0.0.0:9002/docs")
    print("")
    print("Features:")
    print("  - Automatic TTL expiration (cleanup every 5s)")
    print("  - Full Redis-like operations")
    print("  - Key pattern matching")
    print("  - Statistics tracking")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9002,
        log_level="info"
    )
