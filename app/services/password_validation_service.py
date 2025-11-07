import asyncio
from app.core.logging_config import get_logger

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
    pass


class PasswordValidationService:
    def __init__(self):
        self._tools_available = TOOLS_AVAILABLE
        if not self._tools_available:
            logger.warning(
                "Password strength validation tools not available. "
                "Install with: pip install zxcvbn pwnedpasswords"
            )

    def validate_strength(self, password: str) -> dict:
        logger.debug("validation_strength_check_start", password_length=len(password), tools_available=self._tools_available)
        if not self._tools_available:
            logger.warning("Skipping password strength validation - tools not available")
            return {
                "score": 0,
                "feedback": {"warning": "", "suggestions": []},
                "validation_passed": True
            }

        logger.debug("validation_calling_zxcvbn", password_length=len(password))
        results = zxcvbn(password)
        score = results['score']
        logger.debug("validation_zxcvbn_score_received", score=score, password_length=len(password))

        feedback = results.get('feedback', {})
        warning = feedback.get('warning', '')
        suggestions = feedback.get('suggestions', [])
        logger.debug("validation_feedback_extracted", warning=warning, suggestions_count=len(suggestions))

        if score < 3:
            logger.debug("validation_strength_score_too_low", score=score, threshold=3)
            error_msg = f"Weak password detected. {warning}"
            if suggestions:
                error_msg += f" Suggestions: {' '.join(suggestions)}"
            logger.warning(f"Password rejected (score={score}): {warning}")
            raise PasswordValidationError(error_msg)

        logger.debug("validation_strength_score_acceptable", score=score)
        logger.info(f"Password accepted (score={score})")
        return {
            "score": score,
            "feedback": feedback,
            "validation_passed": True
        }

    async def check_breach_status(self, password: str) -> dict:
        logger.debug("validation_breach_check_start", password_length=len(password), tools_available=self._tools_available)
        if not self._tools_available:
            logger.warning("Skipping breach check - tools not available")
            return {
                "leak_count": 0,
                "validation_passed": True
            }

        def blocking_breach_check():
            try:
                logger.debug("validation_calling_pwnedpasswords_api", password_length=len(password))
                pwned = Password(password)
                return pwned.check()
            except Exception as e:
                logger.warning(f"Pwned password check failed: {str(e)}")
                return -1

        try:
            logger.debug("validation_running_breach_check_thread", password_length=len(password))
            leak_count = await asyncio.to_thread(blocking_breach_check)
            logger.debug("validation_breach_check_complete", leak_count=leak_count)

            if leak_count == -1:
                logger.warning("Breach check failed - allowing password through")
                return {
                    "leak_count": -1,
                    "error": "Breach check service unavailable",
                    "validation_passed": True
                }

            if leak_count > 0:
                logger.debug("validation_password_found_in_breaches", leak_count=leak_count)
                error_msg = (
                    "This password has been found in known data breaches. "
                    "Please choose a unique password."
                )
                logger.warning(
                    f"Password rejected (found in {leak_count:,} breaches)"
                )
                raise PasswordValidationError(error_msg)

            logger.debug("validation_password_not_breached", leak_count=leak_count)
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
                "validation_passed": True
            }

    async def validate_password(self, password: str) -> dict:
        logger.debug("validation_password_start", password_length=len(password))
        logger.debug("validation_running_strength_check", password_length=len(password))
        strength_result = self.validate_strength(password)
        logger.debug("validation_strength_check_complete", password_length=len(password), score=strength_result.get("score"))
        logger.debug("validation_running_breach_check", password_length=len(password))
        breach_result = await self.check_breach_status(password)
        logger.debug("validation_breach_check_done", password_length=len(password), leak_count=breach_result.get("leak_count"))

        return {
            "strength": strength_result,
            "breach": breach_result,
            "overall_passed": True
        }


password_validation_service = PasswordValidationService()

def get_password_validation_service() -> PasswordValidationService:
    return password_validation_service
