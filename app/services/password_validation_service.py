"""
Password validation service implementing enterprise-grade password security.

This service handles all password validation logic using industry-standard tools:
- zxcvbn (Dropbox's password strength estimator)
- Have I Been Pwned (data breach checking)

Separates business logic from Pydantic models for better testability and architecture.

All I/O operations are async and non-blocking for optimal performance.
"""
import asyncio
from app.core.logging_config import get_logger

# Probeer de benodigde modules te importeren
try:
    from zxcvbn import zxcvbn
    from pwnedpasswords import Password
    TOOLS_AVAILABLE = True
except ImportError:
    zxcvbn = None
    Password = None
    TOOLS_AVAILABLE = False

logger = get_logger(__name__)


class PasswordValidationError(ValueError):
    """Raised when password validation fails."""
    pass


class PasswordValidationService:
    """
    Service for validating password strength and breach status.

    Uses zxcvbn for strength scoring and Have I Been Pwned for breach detection.
    Following NIST/OWASP password guidelines.

    Score requirements:
    - zxcvbn score >= 3 (strong or very strong)
    - Must NOT appear in known data breaches
    """

    def __init__(self):
        """Initialize password validation service."""
        self._tools_available = TOOLS_AVAILABLE
        if not self._tools_available:
            logger.warning(
                "Password strength validation tools not available. "
                "Install with: pip install zxcvbn pwnedpasswords"
            )

    def validate_strength(self, password: str) -> dict:
        """
        Validate password strength using zxcvbn.

        Args:
            password: Password to validate

        Returns:
            dict: Validation result with score, feedback, etc.

        Raises:
            PasswordValidationError: If password is too weak
        """
        if not self._tools_available:
            logger.warning("Skipping password strength validation - tools not available")
            return {
                "score": 0,
                "feedback": {"warning": "", "suggestions": []},
                "validation_passed": True
            }

        results = zxcvbn(password)
        score = results['score']  # 0-4 scale

        feedback = results.get('feedback', {})
        warning = feedback.get('warning', '')
        suggestions = feedback.get('suggestions', [])

        # Eis een minimum score van 3 (strong)
        if score < 3:
            error_msg = f"Weak password detected. {warning}"
            if suggestions:
                error_msg += f" Suggestions: {' '.join(suggestions)}"
            logger.warning(f"Password rejected (score={score}): {warning}")
            raise PasswordValidationError(error_msg)

        logger.info(f"Password accepted (score={score})")
        return {
            "score": score,
            "feedback": feedback,
            "validation_passed": True
        }

    async def check_breach_status(self, password: str) -> dict:
        """
        Check if password appears in known data breaches via HIBP (async, non-blocking).

        Runs blocking I/O in a thread pool.
        """
        if not self._tools_available:
            logger.warning("Skipping breach check - tools not available")
            return {
                "leak_count": 0,
                "validation_passed": True
            }

        def blocking_breach_check():
            """Run the blocking breach check in a thread."""
            try:
                pwned = Password(password)
                return pwned.check()  # Returns int (number of times found)
            except Exception as e:
                logger.warning(f"Pwned password check failed: {str(e)}")
                return -1  # Indicate check failed

        try:
            leak_count = await asyncio.to_thread(blocking_breach_check)

            if leak_count == -1:
                logger.warning("Breach check failed - allowing password through")
                return {
                    "leak_count": -1,
                    "error": "Breach check service unavailable",
                    "validation_passed": True
                }

            if leak_count > 0:
                error_msg = (
                    "This password has been found in known data breaches. "
                    "Please choose a unique password."
                )
                logger.warning(
                    f"Password rejected (found in {leak_count:,} breaches)"
                )
                raise PasswordValidationError(error_msg)

            logger.info("Password not found in breach database")
            return {
                "leak_count": leak_count,
                "validation_passed": True
            }

        except PasswordValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in breach check: {str(e)}")
            return {
                "leak_count": -1,
                "error": str(e),
                "validation_passed": True  # Allow through if check failed
            }

    async def validate_password(self, password: str) -> dict:
        """
        Complete password validation (strength + breach check) - async version.
        """
        # Stap 1: Check sterkte (synchroon, snel)
        strength_result = self.validate_strength(password)
        
        # Stap 2: Check breaches (asynchroon)
        breach_result = await self.check_breach_status(password)

        return {
            "strength": strength_result,
            "breach": breach_result,
            "overall_passed": True
        }

# Global instance
password_validation_service = PasswordValidationService()

def get_password_validation_service() -> PasswordValidationService:
    """Dependency injection function."""
    return password_validation_service
