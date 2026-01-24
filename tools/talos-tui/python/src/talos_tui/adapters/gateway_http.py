from __future__ import annotations
import logging
from typing import Mapping, Sequence, Optional, Dict, Any, List
import aiohttp
from yarl import URL
from aiohttp import ClientTimeout

from talos_tui.domain.models import Health, MetricsSummary, Peer, Session, VersionInfo
from talos_tui.ports.errors import TuiError
from talos_tui.adapters.redaction import redact_dict

logger = logging.getLogger(__name__)

class HttpGatewayAdapter:
    def __init__(self, base_url: str, session: aiohttp.ClientSession, version: str = "0.1.0"):
        self.base_url = URL(base_url)
        self.session = session
        self.headers = {"User-Agent": f"talos-tui/{version}"}

    async def _get(self, path: str) -> Dict[str, Any]:
        url = self.base_url / path.lstrip("/")
        logger.info(f"Gateway Request: {url}")
        try:
            async with self.session.get(url, headers=self.headers, timeout=ClientTimeout(total=10)) as resp:
                logger.info(f"Gateway Response: {resp.status} for {url}")
                if resp.status >= 400:
                    raise TuiError(
                        kind="BAD_RESPONSE", 
                        message=f"Gateway error {resp.status} at {path}", 
                        status_code=resp.status,
                        retryable=resp.status >= 500
                    )
                # Max payload check (1MB)
                if resp.content_length and resp.content_length > 1_000_000:
                     raise TuiError(kind="PAYLOAD_TOO_LARGE", message=f"Response too large from {path}")
                
                data = await resp.json()
                if not isinstance(data, dict):
                     raise TuiError(kind="BAD_RESPONSE", message=f"Expected dict response from {path}")
                
                # Apply redaction immediately at edge
                return redact_dict(data)
                
        except TuiError:
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Gateway Network Error: {e} for {url}")
            raise TuiError(kind="NETWORK", message=str(e), retryable=True)
        except Exception as e:
            logger.error(f"Gateway Unknown Error: {e} for {url}")
            raise TuiError(kind="UNKNOWN", message=str(e))

    async def get_version(self) -> VersionInfo:
        data = await self._get("version")
        return VersionInfo(**data)

    async def get_health(self) -> Health:
        data = await self._get("healthz")
        return Health(**data)

    async def get_metrics_summary(self) -> MetricsSummary:
        data = await self._get("metrics/summary")
        return MetricsSummary(**data)

    async def list_peers(self) -> Sequence[Peer]:
        data = await self._get("peers")
        # Expecting {"peers": [...]} or list
        items = data.get("peers") if "peers" in data else data
        if not isinstance(items, list):
             return []
        # Cap list size
        return [Peer(**p) for p in items[:500]]

    async def list_sessions(self) -> Sequence[Session]:
        data = await self._get("sessions")
        items = data.get("sessions") if "sessions" in data else data
        if not isinstance(items, list):
            return []
        return [Session(**s) for s in items[:500]]
