"""
Error injection utilities for simulating various failure scenarios.

Supports timeout, server errors, client errors, and custom error scenarios.
"""

import asyncio
from typing import Optional, Literal
from fastapi import Query, HTTPException, status


ErrorType = Literal["timeout", "500", "400", "401", "403", "404", "429", "503"]


async def check_error_simulation(
    simulate_error: Optional[str] = Query(
        None,
        description="Simulate error scenario (timeout|500|400|401|403|404|429|503)"
    )
) -> None:
    """
    Dependency for simulating various error scenarios via query parameter.

    Usage in endpoint:
        @app.get("/example")
        async def example(error_check = Depends(check_error_simulation)):
            return {"message": "success"}

    Query examples:
        GET /example?simulate_error=timeout  -> 408 after 5s delay
        GET /example?simulate_error=500      -> 500 Internal Server Error
        GET /example?simulate_error=400      -> 400 Bad Request

    Args:
        simulate_error: Error type to simulate

    Raises:
        HTTPException: With appropriate status code and message
    """
    if not simulate_error:
        return

    error_map = {
        "timeout": (status.HTTP_408_REQUEST_TIMEOUT, "Request Timeout", 5.0),
        "500": (status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error", 0.0),
        "400": (status.HTTP_400_BAD_REQUEST, "Bad Request", 0.0),
        "401": (status.HTTP_401_UNAUTHORIZED, "Unauthorized", 0.0),
        "403": (status.HTTP_403_FORBIDDEN, "Forbidden", 0.0),
        "404": (status.HTTP_404_NOT_FOUND, "Not Found", 0.0),
        "429": (status.HTTP_429_TOO_MANY_REQUESTS, "Too Many Requests", 0.0),
        "503": (status.HTTP_503_SERVICE_UNAVAILABLE, "Service Unavailable", 0.0),
    }

    if simulate_error in error_map:
        status_code, detail, delay = error_map[simulate_error]
        if delay > 0:
            await asyncio.sleep(delay)
        raise HTTPException(status_code=status_code, detail=detail)


class ErrorSimulator:
    """
    Class-based error simulator for more complex scenarios.

    Usage:
        simulator = ErrorSimulator()
        simulator.set_error_rate("send_email", 0.3)  # 30% failure rate

        if simulator.should_fail("send_email"):
            raise HTTPException(status_code=500, detail="Simulated failure")
    """

    def __init__(self):
        self._error_rates: dict[str, float] = {}
        self._error_scenarios: dict[str, dict] = {}
        self._call_counts: dict[str, int] = {}

    def set_error_rate(self, operation: str, rate: float) -> None:
        """
        Set error rate for an operation (0.0 to 1.0).

        Args:
            operation: Name of the operation
            rate: Failure rate (0.0 = never fail, 1.0 = always fail)
        """
        if not 0.0 <= rate <= 1.0:
            raise ValueError("Error rate must be between 0.0 and 1.0")
        self._error_rates[operation] = rate

    def set_error_scenario(
        self,
        operation: str,
        status_code: int,
        detail: str,
        delay: float = 0.0
    ) -> None:
        """
        Configure specific error scenario for an operation.

        Args:
            operation: Name of the operation
            status_code: HTTP status code to return
            detail: Error detail message
            delay: Optional delay before raising error (seconds)
        """
        self._error_scenarios[operation] = {
            "status_code": status_code,
            "detail": detail,
            "delay": delay
        }

    def should_fail(self, operation: str) -> bool:
        """
        Determine if operation should fail based on configured error rate.

        Args:
            operation: Name of the operation

        Returns:
            True if operation should fail
        """
        import random

        self._call_counts[operation] = self._call_counts.get(operation, 0) + 1
        rate = self._error_rates.get(operation, 0.0)

        return random.random() < rate

    async def raise_if_configured(self, operation: str) -> None:
        """
        Raise HTTPException if error scenario is configured for operation.

        Args:
            operation: Name of the operation

        Raises:
            HTTPException: If error scenario configured and should fail
        """
        if operation not in self._error_scenarios:
            return

        if not self.should_fail(operation):
            return

        scenario = self._error_scenarios[operation]
        if scenario["delay"] > 0:
            await asyncio.sleep(scenario["delay"])

        raise HTTPException(
            status_code=scenario["status_code"],
            detail=scenario["detail"]
        )

    def get_stats(self, operation: str) -> dict:
        """
        Get statistics for an operation.

        Args:
            operation: Name of the operation

        Returns:
            Dictionary with call count and configured error rate
        """
        return {
            "operation": operation,
            "call_count": self._call_counts.get(operation, 0),
            "error_rate": self._error_rates.get(operation, 0.0),
            "has_scenario": operation in self._error_scenarios
        }

    def reset(self) -> None:
        """Reset all error configurations and statistics."""
        self._error_rates.clear()
        self._error_scenarios.clear()
        self._call_counts.clear()
