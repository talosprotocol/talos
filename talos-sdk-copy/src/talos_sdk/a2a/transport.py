"""A2A HTTP Transport with retry logic and error mapping."""

import asyncio
import random

import httpx

from talos_sdk.wallet import Wallet

from .errors import A2AError, A2ATransportError, raise_mapped_error
from .models import (
    EncryptedFrame,
    ErrorResponse,
    FrameListResponse,
    FrameSendResponse,
    GroupResponse,
    SessionResponse,
)


class A2ATransport:
    """HTTP transport for A2A gateway endpoints.

    Features:
    - Wallet-based request signing
    - Exponential backoff retry on 5xx and network errors
    - 4xx error mapping to typed exceptions
    - Dependency-injected httpx.AsyncClient

    Usage:
        transport = A2ATransport("https://gateway.example.com", wallet)
        try:
            resp = await transport.create_session("responder-id")
        finally:
            await transport.aclose()
    """

    def __init__(
        self,
        gateway_url: str,
        wallet: Wallet,
        http: httpx.AsyncClient | None = None,
    ):
        self._gateway_url = gateway_url.rstrip("/")
        self._wallet = wallet
        self._http = http or httpx.AsyncClient()
        self._owns_http = http is None

    async def aclose(self) -> None:
        """Close the HTTP client if owned."""
        if self._owns_http:
            await self._http.aclose()

    def _sign_headers(
        self, method: str, path: str, body: dict | None, params: dict | None
    ) -> dict:
        """Sign the request and return headers."""
        # Build query string for signing (canonical ordering)
        query = ""
        if params:
            query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return self._wallet.sign_http_request(method, path, query=query, body=body)

    async def _request(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        params: dict | None = None,
    ) -> dict:
        """Execute HTTP request with retry and error mapping."""
        url = f"{self._gateway_url}{path}"
        headers = self._sign_headers(method, path, body, params)

        max_attempts = 4
        base_delay = 0.2

        for attempt in range(1, max_attempts + 1):
            try:
                kwargs: dict = {"params": params, "headers": headers}
                if body is not None:
                    kwargs["json"] = body

                # Inject Trace Context if available
                # We check if opentelemetry is installed and a trace is active.
                # Since SDK usage is library-based, we don't force OTEL dependency.
                # We try import inside method or use a safer approach.
                try:
                    from opentelemetry import propagate
                    propagate.inject(headers)
                except ImportError:
                    pass
                
                resp = await self._http.request(method, url, **kwargs)
            except httpx.RequestError as e:
                if attempt == max_attempts:
                    raise A2ATransportError(f"Request failed: {e}")
                await asyncio.sleep(
                    base_delay * (2 ** (attempt - 1)) + random.random() * 0.05
                )
                continue

            # Retry on 5xx
            if resp.status_code >= 500 and attempt < max_attempts:
                await asyncio.sleep(
                    base_delay * (2 ** (attempt - 1)) + random.random() * 0.05
                )
                continue

            # Map 4xx errors to typed exceptions
            if resp.status_code >= 400:
                try:
                    err = ErrorResponse.model_validate(resp.json())
                    raise_mapped_error(err, status_code=resp.status_code)
                except A2AError:
                    raise
                except Exception:
                    raise A2ATransportError("Gateway error", resp.status_code)

            return resp.json()

        raise A2ATransportError("Unexpected transport failure")

    # === Session Routes ===

    async def create_session(
        self, responder_id: str, *, expires_at: str | None = None
    ) -> SessionResponse:
        """Create a new A2A session."""
        body: dict = {"responder_id": responder_id}
        if expires_at:
            body["expires_at"] = expires_at
        data = await self._request("POST", "/a2a/v1/sessions", body)
        return SessionResponse.model_validate(data)

    async def accept_session(self, session_id: str) -> SessionResponse:
        """Accept a pending session as responder."""
        data = await self._request(
            "POST", f"/a2a/v1/sessions/{session_id}/accept", {}
        )
        return SessionResponse.model_validate(data)

    async def rotate_session(self, session_id: str) -> SessionResponse:
        """Rotate session keys."""
        data = await self._request(
            "POST", f"/a2a/v1/sessions/{session_id}/rotate", {}
        )
        return SessionResponse.model_validate(data)

    async def close_session(self, session_id: str) -> SessionResponse:
        """Close a session."""
        data = await self._request("DELETE", f"/a2a/v1/sessions/{session_id}")
        return SessionResponse.model_validate(data)

    # === Frame Routes ===

    async def send_frame(
        self, session_id: str, frame: EncryptedFrame
    ) -> FrameSendResponse:
        """Send an encrypted frame."""
        body = {"frame": frame.model_dump(mode="json", exclude_none=True)}
        data = await self._request(
            "POST", f"/a2a/v1/sessions/{session_id}/frames", body
        )
        return FrameSendResponse.model_validate(data)

    async def receive_frames(
        self, session_id: str, *, cursor: str | None = None, limit: int = 100
    ) -> FrameListResponse:
        """Receive frames with cursor pagination."""
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        # No body for GET
        data = await self._request(
            "GET", f"/a2a/v1/sessions/{session_id}/frames", params=params
        )
        return FrameListResponse.model_validate(data)

    # === Group Routes ===

    async def create_group(self, name: str | None = None) -> GroupResponse:
        """Create a new group."""
        body: dict = {}
        if name:
            body["name"] = name
        data = await self._request("POST", "/a2a/v1/groups", body)
        return GroupResponse.model_validate(data)

    async def add_member(self, group_id: str, member_id: str) -> GroupResponse:
        """Add a member to a group."""
        body = {"member_id": member_id}
        data = await self._request(
            "POST", f"/a2a/v1/groups/{group_id}/members", body
        )
        return GroupResponse.model_validate(data)

    async def remove_member(self, group_id: str, member_id: str) -> GroupResponse:
        """Remove a member from a group."""
        data = await self._request(
            "DELETE", f"/a2a/v1/groups/{group_id}/members/{member_id}"
        )
        return GroupResponse.model_validate(data)

    async def close_group(self, group_id: str) -> GroupResponse:
        """Close a group."""
        data = await self._request("DELETE", f"/a2a/v1/groups/{group_id}")
        return GroupResponse.model_validate(data)
