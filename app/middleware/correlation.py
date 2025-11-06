from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default=None)


async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    correlation_id_var.set(correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id

    return response
