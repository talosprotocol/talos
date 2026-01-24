from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, DataTable, Label
from textual.containers import Container
from rich.text import Text

class AuditViewer(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="audit_container"):
            yield Label("AUDIT EVENT LOG", classes="title")
            yield DataTable(cursor_type="row", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("!", "Timestamp", "Type", "ID")

    def _get_severity(self, event_type: str) -> tuple[str, str]:
        """Maps event types to severity markers and CSS classes."""
        etype = event_type.lower()
        if any(w in etype for w in ["error", "fail", "critical"]):
            return "E", "severity-error"
        if any(w in etype for w in ["warn", "alert", "deny"]):
            return "W", "severity-warn"
        return "I", "severity-info"

    def add_events(self, events: list) -> None:
        table = self.query_one(DataTable)
        for e in events:
            sev_char, sev_class = self._get_severity(e.event_type)
            sev_marker = Text(sev_char, style=f"bold")
            
            # Textual's DataTable can style cells by adding them as styled strings or Rich objects
            # The TCSS handles the color via classes if we were using widgets, 
            # but for DataTable cells we'll use Rich's native styling for precision.
            color_map = {
                "severity-error": "#FF007A",
                "severity-warn": "#F1FA8C",
                "severity-info": "#00FF9C"
            }
            color = color_map.get(sev_class, "#E6EDF3")
            
            table.add_row(
                Text(sev_char, style=f"bold {color}"),
                Text(e.ts, style=color),
                Text(e.event_type, style=color),
                Text(e.id, style="dim")
            )
            
        table.scroll_end(animate=False)
