from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Digits
from textual.containers import Grid, Container, Vertical
from textual.reactive import reactive

class MetricCard(Container):
    """A premium card for displaying a single metric."""
    value = reactive("0")
    
    def __init__(self, title: str, id: str):
        self.title_text = title
        super().__init__(id=id)
        
    def compose(self) -> ComposeResult:
        yield Label(self.title_text, classes="metric-title")
        with Vertical(classes="metric-value-container"):
            yield Digits(self.value, classes="metric-value")
        
    def update_value(self, val: str) -> None:
        self.value = val

class StatusDashboard(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="dashboard_container"):
            yield Label("NETWORK STATUS OVERVIEW", classes="title")
            with Grid():
                yield MetricCard("Connected Peers", id="peers")
                yield MetricCard("Active Sessions", id="sessions")
                yield MetricCard("Latency p50 (ms)", id="p50")
                yield MetricCard("Latency p95 (ms)", id="p95")
        yield Footer()

    def update_metrics(self, metrics: dict) -> None:
        self.query_one("#peers", MetricCard).update_value(str(metrics.get("connected_peers", 0)))
        self.query_one("#sessions", MetricCard).update_value(str(metrics.get("active_sessions", 0)))
        self.query_one("#p50", MetricCard).update_value(f"{metrics.get('latency_p50_ms', 0.0):.1f}")
        self.query_one("#p95", MetricCard).update_value(f"{metrics.get('latency_p95_ms', 0.0):.1f}")
