"""Configuration Service Entry Point."""

from collections.abc import Awaitable

import uvicorn

# pylint: disable=import-error
from api.routes import limiter, router  # type: ignore
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.config import SETTINGS  # type: ignore

app = FastAPI(
    title="Talos Configuration Service",
    version=SETTINGS.VERSION,
    description="Configuration management and distribution for the Talos system.",  # noqa: E501
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


async def _rate_limit_handler_wrapper(
    request: Request, exc: RateLimitExceeded
) -> Response | Awaitable[Response]:
    """Type-safe wrapper for the rate limit exceeded handler."""
    return _rate_limit_exceeded_handler(request, exc)


# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler_wrapper)

# CORS (Restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/config")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=SETTINGS.DEV_MODE,
    )

# Final Quality Check Sync - v3
