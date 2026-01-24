# Talos TUI Repository Policy

## Security Invariants (Stop-Ship)
1. **No Plaintext Secrets**: All secrets must be redacted by default.
2. **Read-Only Control Plane**: No file writes (config/env) and no command execution.
3. **Unified Auth**: Must use `talos-sdk-py` identity primitives. No backdoors.
4. **Network Allowlist**: Connect only to configured endpoints.
5. **Bounded Resources**: Ring buffers must have hard caps.

## Performance Invariants
1. **Latency Budget**: < 100ms p95 for keypress to visual response.
2. **Ingestion Rate**: Sustain 50-200 events/sec without stutter.
3. **Throttling**: UI must render at a fixed cadence (max 10Hz).
4. **Parsing**: JSON parsing must happen off the UI thread.
5. **Logging**: Never log request headers. Log metadata only.
