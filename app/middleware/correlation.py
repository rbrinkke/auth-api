from contextvars import ContextVar
from uuid import uuid4

from fastapi import Request

trace_id_var: ContextVar[str] = ContextVar("trace_id", default=None)


async def trace_id_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID") or str(uuid4())
    trace_id_var.set(trace_id)

    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id

    return response
