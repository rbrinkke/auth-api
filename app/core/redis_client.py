"""
Redis client for managing temporary tokens and blacklists.

Key Patterns:
- verify_token:{token} → user_id (TTL: 24h)
- verify_user:{user_id} → token (TTL: 24h)
- reset_token:{token} → user_id (TTL: 1h)
- reset_user:{user_id} → token (TTL: 1h)
- blacklist_jti:{jti} → "1" (TTL: 30d)
"""
from typing import Optional
from uuid import UUID

import redis.asyncio as redis

from app.config import settings


class RedisClient:
    """Async Redis client wrapper for token management."""
    
    def __init__(self):
        self.client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Establish connection to Redis."""
        self.client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
    
    # ========== Verification Tokens ==========
    
    async def set_verification_token(self, token: str, user_id: UUID) -> None:
        """
        Store a verification token in Redis.
        Also stores reverse lookup to prevent multiple active tokens.
        
        Args:
            token: The verification token
            user_id: The user's UUID
        """
        user_id_str = str(user_id)
        
        # Check if user already has a token
        old_token = await self.client.get(f"verify_user:{user_id_str}")
        if old_token:
            # Delete the old token
            await self.client.delete(f"verify_token:{old_token}")
        
        # Store new token
        await self.client.setex(
            f"verify_token:{token}",
            settings.verification_token_ttl,
            user_id_str
        )
        
        # Store reverse lookup
        await self.client.setex(
            f"verify_user:{user_id_str}",
            settings.verification_token_ttl,
            token
        )
    
    async def get_user_id_from_verification_token(self, token: str) -> Optional[UUID]:
        """
        Retrieve user ID from a verification token.
        
        Args:
            token: The verification token
            
        Returns:
            User UUID if token exists and is valid, None otherwise
        """
        user_id_str = await self.client.get(f"verify_token:{token}")
        if user_id_str:
            try:
                return UUID(user_id_str)
            except ValueError:
                return None
        return None
    
    async def delete_verification_token(self, token: str, user_id: UUID) -> None:
        """
        Delete a verification token and its reverse lookup.
        
        Args:
            token: The verification token
            user_id: The user's UUID
        """
        await self.client.delete(
            f"verify_token:{token}",
            f"verify_user:{str(user_id)}"
        )
    
    # ========== Password Reset Tokens ==========
    
    async def set_reset_token(self, token: str, user_id: UUID) -> None:
        """
        Store a password reset token in Redis.
        Also stores reverse lookup to prevent multiple active tokens.
        
        Args:
            token: The reset token
            user_id: The user's UUID
        """
        user_id_str = str(user_id)
        
        # Check if user already has a token
        old_token = await self.client.get(f"reset_user:{user_id_str}")
        if old_token:
            # Delete the old token
            await self.client.delete(f"reset_token:{old_token}")
        
        # Store new token
        await self.client.setex(
            f"reset_token:{token}",
            settings.reset_token_ttl,
            user_id_str
        )
        
        # Store reverse lookup
        await self.client.setex(
            f"reset_user:{user_id_str}",
            settings.reset_token_ttl,
            token
        )
    
    async def get_user_id_from_reset_token(self, token: str) -> Optional[UUID]:
        """
        Retrieve user ID from a password reset token.
        
        Args:
            token: The reset token
            
        Returns:
            User UUID if token exists and is valid, None otherwise
        """
        user_id_str = await self.client.get(f"reset_token:{token}")
        if user_id_str:
            try:
                return UUID(user_id_str)
            except ValueError:
                return None
        return None
    
    async def delete_reset_token(self, token: str, user_id: UUID) -> None:
        """
        Delete a password reset token and its reverse lookup.
        
        Args:
            token: The reset token
            user_id: The user's UUID
        """
        await self.client.delete(
            f"reset_token:{token}",
            f"reset_user:{str(user_id)}"
        )
    
    # ========== Refresh Token Blacklist ==========
    
    async def blacklist_refresh_token(self, jti: str) -> None:
        """
        Add a refresh token's JTI to the blacklist.
        
        Args:
            jti: The JWT ID to blacklist
        """
        # TTL = refresh token lifetime
        ttl = settings.jwt_refresh_token_expire_days * 86400
        await self.client.setex(f"blacklist_jti:{jti}", ttl, "1")
    
    async def is_token_blacklisted(self, jti: str) -> bool:
        """
        Check if a refresh token is blacklisted.
        
        Args:
            jti: The JWT ID to check
            
        Returns:
            True if blacklisted, False otherwise
        """
        result = await self.client.exists(f"blacklist_jti:{jti}")
        return result > 0


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """
    Dependency for getting Redis client in route handlers.
    
    Usage:
        @router.post("/login")
        async def login(redis: RedisClient = Depends(get_redis)):
            await redis.set_verification_token(...)
    """
    return redis_client
