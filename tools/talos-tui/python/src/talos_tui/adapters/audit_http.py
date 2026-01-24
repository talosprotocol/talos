from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List
import aiohttp
from yarl import URL
from aiohttp import ClientTimeout

from talos_tui.domain.models import AuditPage, AuditEvent, VersionInfo, Health
from talos_tui.ports.errors import TuiError
from talos_tui.adapters.redaction import redact_dict

logger = logging.getLogger(__name__)

class HttpAuditAdapter:
    def __init__(self, base_url: str, session: aiohttp.ClientSession, version: str = "0.1.0"):
        self.base_url = URL(base_url)
        self.session = session
        self.headers = {"User-Agent": f"talos-tui/{version}"}

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self.base_url / path.lstrip("/")
        logger.info(f"Audit Request: {url}")
        try:
            async with self.session.get(url, headers=self.headers, params=params, timeout=ClientTimeout(total=10)) as resp:
                logger.info(f"Audit Response: {resp.status} for {url}")
                if resp.status >= 400:
                    raise TuiError(
                        kind="BAD_RESPONSE",
                        message=f"Audit error {resp.status} at {path}",
                        status_code=resp.status,
                        retryable=resp.status >= 500
                    )
                
                if resp.content_length and resp.content_length > 1_000_000:
                     raise TuiError(kind="PAYLOAD_TOO_LARGE", message=f"Response too large from {path}")

                data = await resp.json()
                if not isinstance(data, dict):
                     raise TuiError(kind="BAD_RESPONSE", message=f"Expected dict response from {path}")
                
                return redact_dict(data)

        except TuiError:
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Audit Network Error: {e} for {url}")
            raise TuiError(kind="NETWORK", message=str(e), retryable=True)
        except Exception as e:
            logger.error(f"Audit Unknown Error: {e} for {url}")
            raise TuiError(kind="UNKNOWN", message=str(e))

    async def get_version(self) -> VersionInfo:
        data = await self._get("version")
        return VersionInfo(**data)

    async def get_health(self) -> Health:
        data = await self._get("health")
        return Health(**data)

    async def list_events(self, limit: int, before: Optional[str]) -> AuditPage:
        params = {"limit": str(limit)}
        if before:
            params["before"] = before
            
        data = await self._get("api/events", params=params)
        
        # Safe extraction
        items_data = data.get("items", [])
        if not isinstance(items_data, list):
            items_data = []
            
        items = [AuditEvent(**i) for i in items_data]
        return AuditPage(
            items=items,
            next_cursor=data.get("next_cursor"),
            has_more=data.get("has_more", False)
        )
