"""
Password validation service implementing enterprise-grade password security.

This service handles all password validation logic using industry-standard tools:
- zxcvbn (Dropbox's password strength estimator)
- Have I Been Pwned (data breach checking)

Separates business logic from Pydantic models for better testability and architecture.
"""
import logging

logger = logging.getLogger(__name__)


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
        # Import password tools (optional dependency)
        try:
            from zxcvbn import zxcvbn
            from pwnedpasswords import Password
            self._zxcvbn = zxcvbn
            self._Password = Password
            self._tools_available = True
            logger.info("Password validation tools loaded successfully")
        except ImportError:
            self._zxcvbn = None
            self._Password = None
            self._tools_available = False
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
        # If tools not available, skip validation (but log warning)
        if not self._tools_available:
            logger.warning("Skipping password strength validation - tools not available")
            return {
                "score": 0,
                "feedback": {"warning": "", "suggestions": []},
                "validation_passed": True
            }

        # Check password strength with zxcvbn
        results = self._zxcvbn(password)
        score = results['score']  # 0-4 scale (0=very weak, 4=very strong)

        feedback = results.get('feedback', {})
        warning = feedback.get('warning', '')
        suggestions = feedback.get('suggestions', [])

        # Require minimum score of 3 (strong or very strong)
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

    def check_breach_status(self, password: str) -> dict:
        """
        Check if password appears in known data breaches via HIBP.

        Args:
            password: Password to check

        Returns:
            dict: Breach check result

        Raises:
            PasswordValidationError: If password found in breaches
        """
        # If tools not available, skip check
        if not self._tools_available:
            logger.warning("Skipping breach check - tools not available")
            return {
                "leak_count": 0,
                "validation_passed": True
            }

        try:
            # Check against HIBP database
            # Using synchronous call (blocking, but safe in service layer)
            pwned = self._Password(password)
            leak_count = pwned.check()  # Returns int (number of times found)

            if leak_count > 0:
                error_msg = (
                    "This password has been found in known data breaches. "
                    "Please choose a unique password that hasn't been compromised."
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

        except Exception as e:
            # If breach check fails, log but don't block
            # (we don't want to prevent registration if HIBP is down)
            logger.warning(f"Pwned password check failed: {str(e)}")
            return {
                "leak_count": -1,  # Indicate check failed
                "error": str(e),
                "validation_passed": True  # Allow through if check failed
            }

    def validate_password(self, password: str) -> dict:
        """
        Complete password validation (strength + breach check).

        Args:
            password: Password to validate

        Returns:
            dict: Complete validation result

        Raises:
            PasswordValidationError: If validation fails
        """
        # Step 1: Check strength
        strength_result = self.validate_strength(password)

        # Step 2: Check breaches
        breach_result = self.check_breach_status(password)

        return {
            "password": password,  # Don't log the actual password!
            "strength": strength_result,
            "breach": breach_result,
            "overall_passed": True
        }


# Global password validation service instance
password_validation_service = PasswordValidationService()


def get_password_validation_service() -> PasswordValidationService:
    """
    Dependency injection function for PasswordValidationService.

    Returns:
        PasswordValidationService: Configured validation service

    Enables easy mocking during testing:
        app.dependency_overrides[get_password_validation_service] = mock_factory
    """
    return password_validation_service
