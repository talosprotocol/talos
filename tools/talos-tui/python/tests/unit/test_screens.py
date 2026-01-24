import pytest
from talos_tui.ui.screens.dashboard import StatusDashboard, MetricWidget
from talos_tui.ui.screens.audit import AuditViewer
from talos_tui.domain.models import AuditEvent

# We can test screen logic without mounting it fully in an App context
# by instantiating widgets directly or relying on Textual's headless capabilities if needed.
# For now, we test the logic methods assuming queries work or mocking them.
# Since querying requires a mounted app usually, we'll try to rely on patching `query_one`
# or just instantiation coverage + method calls if they don't depend on DOM.

# Actually, Textual widgets need an app to function properly for `query`.
# We'll skip complex UI testing for V1 and focus on testing the data methods if possible,
# or just accept lower coverage on UI provided Supervisor bumps us up.
# Let's try to mock `query_one` which is what `update_metrics` calls.

from unittest.mock import MagicMock

def test_dashboard_update_metrics():
    dash = StatusDashboard()
    
    # Mock query_one to return a mock widget that accepts update_value
    mock_widget = MagicMock()
    dash.query_one = MagicMock(return_value=mock_widget)
    
    dash.update_metrics({
        "connected_peers": 10,
        "active_sessions": 5,
        "latency_p50_ms": 12.5,
        "latency_p95_ms": 40.2
    })
    
    # Verify calls
    assert dash.query_one.call_count == 4
    # Check calls
    calls = dash.query_one.call_args_list
    assert calls[0][0][0] == "#peers"
    assert calls[1][0][0] == "#sessions"

def test_audit_add_events():
    audit = AuditViewer()
    mock_table = MagicMock()
    audit.query_one = MagicMock(return_value=mock_table)
    
    events = [
        AuditEvent(id="1", ts="2023", event_type="login", payload={})
    ]
    
    audit.add_events(events)
    
    mock_table.add_row.assert_called_with("2023", "login", "1")
