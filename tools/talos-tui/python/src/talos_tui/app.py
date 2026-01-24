import asyncio
import os
import logging
from typing import Optional, Any

# Configure logging early and REDIRECT to file to keep terminal clean for Textual
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename="talos-tui.log",
    filemode="a"
)
logger = logging.getLogger(__name__)

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label, LoadingIndicator
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.binding import Binding
from textual.theme import Theme

from talos_tui.runtime.supervisor import Supervisor
from talos_tui.adapters.gateway_http import HttpGatewayAdapter
from talos_tui.adapters.audit_http import HttpAuditAdapter
from talos_tui.adapters.mock import MockGatewayAdapter, MockAuditAdapter
from talos_tui.ui.screens.dashboard import StatusDashboard
from talos_tui.ui.screens.audit import AuditViewer
from talos_tui.ports.errors import TuiError

# Constants
GATEWAY_URL = os.getenv("TALOS_GATEWAY_URL", "http://localhost:8000")
AUDIT_URL = os.getenv("TALOS_AUDIT_URL", "http://localhost:8001")
USE_MOCK = os.getenv("TALOS_TUI_MOCK", "0") == "1"
CONTRACTS_MAJOR_VERSION = "1" # Supported major version
POLL_INTERVAL_SEC = 2.0  # 0.5Hz polling to start safe

class StartupScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Connecting to Talos Network...", id="status_label"),
            LoadingIndicator()
        )

TALOS_COMMAND_CENTER = Theme(
    name="talos-command-center",
    primary="#14FFEC",
    secondary="#7AA2F7",
    accent="#14FFEC",
    foreground="#E6EDF3",
    background="#0A0E14",
    success="#00FF9C",
    warning="#F1FA8C",
    error="#FF007A",
    surface="#161B22",
    panel="#161B22",
    dark=True,
)

class ErrorScreen(Screen):
    def __init__(self, message: str):
        self.message = message
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Container(Label(f"CRITICAL ERROR: {self.message}", classes="error-msg"))

class TalosTuiApp(App):
    TITLE = "TALOS COMMAND CENTER"
    CSS_PATH = "ui/talos.tcss"
    
    BINDINGS = [
        Binding("d", "show_dashboard", "Dashboard"),
        Binding("a", "show_audit", "Audit Logs"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.supervisor = Supervisor()
        self.gateway: Any = None
        self.audit: Any = None
        self.dashboard_screen = StatusDashboard()
        self.audit_screen = AuditViewer()

    async def on_mount(self) -> None:
        self.register_theme(TALOS_COMMAND_CENTER)
        self.theme = "talos-command-center"
        await self.supervisor.start()
        
        if USE_MOCK:
            self.gateway = MockGatewayAdapter()
            self.audit = MockAuditAdapter()
            self.sub_title = "MODE: MOCK / DEMO"
        else:
            self.gateway = HttpGatewayAdapter(GATEWAY_URL, self.supervisor.session)
            self.audit = HttpAuditAdapter(AUDIT_URL, self.supervisor.session)
        
        self.install_screen(self.dashboard_screen, name="dashboard")
        self.install_screen(self.audit_screen, name="audit")
        
        self.push_screen(StartupScreen())
        self.supervisor.spawn(self.perform_handshake(), scope="handshake")

    async def perform_handshake(self) -> None:
        logger.info(f"Starting handshake with Gateway: {GATEWAY_URL} and Audit: {AUDIT_URL}")
        max_retries = 10
        initial_delay = 1.0
        max_delay = 10.0
        
        for attempt in range(max_retries):
            try:
                # 1. Check Health first
                gw_health = await self.gateway.get_health()
                audit_health = await self.audit.get_health()
                
                if not gw_health.ok or not audit_health.ok:
                    raise TuiError(kind="NOT_READY", message="One or more services reported unhealthy")

                # 2. Get Versions
                gw_ver = await self.gateway.get_version()
                audit_ver = await self.audit.get_version()
                
                gw_major = gw_ver.contracts_version.split(".")[0]
                if gw_major != CONTRACTS_MAJOR_VERSION:
                    raise TuiError(kind="INCOMPATIBLE", message=f"Gateway contracts version {gw_ver.contracts_version} mismatch")
                    
                self.sub_title = f"GW: {gw_ver.service_version} | Audit: {audit_ver.service_version}"
                
                # Start polling loops
                self.supervisor.spawn(self.poll_metrics(), scope="app_global")
                self.supervisor.spawn(self.poll_audit(), scope="app_global")
                
                self.switch_screen("dashboard")
                logger.info("Handshake successful")
                return # Success!
                
            except TuiError as e:
                if e.kind == "INCOMPATIBLE":
                    self.push_screen(ErrorScreen(f"INCOMPATIBLE CONTRACTS: {e.message}"))
                    return
                logger.warning(f"Handshake attempt {attempt + 1} failed: {e.message}")
            except Exception as e:
                logger.warning(f"Handshake attempt {attempt + 1} failed with error: {str(e)}")
            
            # Exponential backoff: delay = initial * 2^attempt, capped at max_delay
            delay = min(max_delay, initial_delay * (2 ** attempt))
            logger.info(f"Retrying in {delay:.1f}s...")
            await asyncio.sleep(delay)
            
        self.push_screen(ErrorScreen(f"Connection Failed after {max_retries} attempts"))

    async def poll_metrics(self) -> None:
        while True:
            try:
                metrics = await self.gateway.get_metrics_summary()
                self.dashboard_screen.update_metrics(metrics.dict())
            except Exception:
                pass # Silent fail on poll, retry next tick
            await asyncio.sleep(POLL_INTERVAL_SEC)

    async def poll_audit(self) -> None:
        cursor = None
        while True:
            try:
                page = await self.audit.list_events(limit=50, before=cursor)
                if page.items:
                    self.audit_screen.add_events(page.items)
                    # Simple cursor logic for now
                    if page.next_cursor:
                        cursor = page.next_cursor
            except Exception:
                pass
            await asyncio.sleep(POLL_INTERVAL_SEC)

    def action_show_dashboard(self) -> None:
        self.switch_screen("dashboard")

    def action_show_audit(self) -> None:
        self.switch_screen("audit")

    async def on_unmount(self) -> None:
        await self.supervisor.stop()

def main() -> None:
    app = TalosTuiApp()
    app.run()
