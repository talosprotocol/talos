"""
Terminal MCP Adapter - Main Application

MCP Server implementing the Terminal Adapter specification with:
- Structured terminal:* tools
- Command classification and policy enforcement
- Session-based Merkle audit trees
- Integration with TGA for HIGH_RISK approval
"""

import os
import asyncio
import logging
import subprocess
import pty
import select
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Body, Header
from pydantic import BaseModel, Field

from terminal_adapter.domain import (
    RiskLevel,
    PolicyManifest,
    CommandClassifier,
    SessionManager,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("terminal-adapter")


# ============================================================================
# Request/Response Models (based on talos-contracts schemas)
# ============================================================================

class TerminalExecuteRequest(BaseModel):
    """Request to execute a terminal command."""
    command: str = Field(..., description="Binary to execute")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    cwd: Optional[str] = Field(None, description="Working directory")
    env: Optional[Dict[str, str]] = Field(None, description="Environment overrides")
    timeout_ms: int = Field(30000, ge=1000, le=300000, description="Timeout in ms")
    session_id: Optional[str] = Field(None, description="Reuse existing session")
    risk_level: Optional[str] = Field(None, description="Declared risk level")
    idempotency_key: Optional[str] = Field(None, description="For write operations")


class TerminalExecuteResponse(BaseModel):
    """Response from terminal execution."""
    session_id: str
    exit_code: Optional[int] = None
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False
    audit_hash: str = ""
    input_required: bool = False


class TerminalWriteInputRequest(BaseModel):
    """Request to write stdin to a running session."""
    session_id: str
    data: str


class TerminalAnchorResponse(BaseModel):
    """Response from session anchor."""
    session_id: str
    merkle_root: str
    action_count: int


class SessionInfo(BaseModel):
    """Session information."""
    session_id: str
    created_at: str
    action_count: int
    is_active: bool


# ============================================================================
# Application State
# ============================================================================

class AppState:
    """Global application state."""
    classifier: Optional[CommandClassifier] = None
    session_manager: Optional[SessionManager] = None
    project_root: str = ""
    paranoid_mode: bool = False


state = AppState()


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    project_root = os.getenv("TALOS_PROJECT_ROOT", os.getcwd())
    manifest_path = os.getenv("TALOS_POLICY_MANIFEST")
    
    state.project_root = project_root
    
    # Load policy manifest if available
    manifest = None
    if manifest_path and os.path.exists(manifest_path):
        try:
            manifest = PolicyManifest.load(manifest_path)
            if not manifest.verify_signature(b""):  # TODO: Load supervisor public key
                logger.warning("Policy manifest signature invalid - entering Paranoid Mode")
                state.paranoid_mode = True
        except Exception as e:
            logger.warning(f"Failed to load policy manifest: {e} - entering Paranoid Mode")
            state.paranoid_mode = True
    
    # Initialize classifier
    state.classifier = CommandClassifier(manifest=manifest, paranoid_mode=state.paranoid_mode)
    
    # Initialize session manager with anchor callback
    async def anchor_to_audit(session_id: str, merkle_root: str):
        """Callback to anchor session to Talos Audit Service."""
        # TODO: Implement actual audit service call
        logger.info(f"Anchoring {session_id}: {merkle_root[:16]}...")
    
    state.session_manager = SessionManager(
        project_root=project_root,
        anchor_callback=anchor_to_audit
    )
    
    # Start periodic anchoring
    await state.session_manager.start_anchor_loop()
    
    logger.info(f"Terminal Adapter started (project_root={project_root}, paranoid={state.paranoid_mode})")
    
    yield
    
    # Shutdown
    if state.session_manager:
        await state.session_manager.stop_anchor_loop()
    
    logger.info("Terminal Adapter stopped")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Talos Terminal MCP Adapter",
    version="1.0.0",
    description="Structured terminal access for AI agents with policy enforcement and audit logging",
    lifespan=lifespan
)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "terminal-adapter",
        "paranoid_mode": state.paranoid_mode,
    }


# ============================================================================
# Core Terminal Tools
# ============================================================================

@app.post("/tools/terminal:execute", response_model=TerminalExecuteResponse)
async def terminal_execute(
    request: TerminalExecuteRequest = Body(...),
    x_talos_principal: Optional[str] = Header(None, alias="X-Talos-Principal"),
    x_talos_capability: Optional[str] = Header(None, alias="X-Talos-Capability"),
):
    """
    Execute a terminal command.
    
    Risk-based execution:
    - READ: Execute immediately (bypass Supervisor)
    - WRITE: Block until Supervisor approval
    - HIGH_RISK: Halt and escalate to Supervisor
    """
    if not state.classifier or not state.session_manager:
        raise HTTPException(status_code=503, detail="Adapter not initialized")
    
    # 1. Classify command
    classification = state.classifier.classify(request.command, request.args)
    
    # Check if blocked
    if classification.is_blocked:
        raise HTTPException(
            status_code=403,
            detail=f"Command blocked: {classification.block_reason}"
        )
    
    # 2. Validate working directory (must be under project root)
    cwd = request.cwd or state.project_root
    if not os.path.abspath(cwd).startswith(os.path.abspath(state.project_root)):
        raise HTTPException(
            status_code=403,
            detail=f"Working directory must be under project root: {state.project_root}"
        )
    
    # 3. Handle based on risk level
    if classification.risk_level == RiskLevel.HIGH_RISK:
        # Halt - require Supervisor approval (not implemented yet)
        raise HTTPException(
            status_code=403,
            detail=f"HIGH_RISK command requires Supervisor approval: {request.command}"
        )
    
    if classification.risk_level == RiskLevel.WRITE:
        # In v1, WRITE also blocks for Supervisor (per spec constraint)
        # For now, we allow in dev mode
        if os.getenv("TALOS_ENV") != "dev":
            raise HTTPException(
                status_code=403,
                detail=f"WRITE command requires Supervisor approval: {request.command}"
            )
    
    # 4. Get or create session
    if request.session_id:
        session = state.session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = state.session_manager.create_session()
    
    # 5. Execute command
    try:
        stdout, stderr, exit_code = await _execute_command(
            command=request.command,
            args=request.args,
            cwd=cwd,
            env=request.env,
            timeout_ms=request.timeout_ms
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Command timed out")
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
    
    # 6. Record action to session (WAL + Merkle tree)
    audit_hash = state.session_manager.record_action(
        session_id=session.session_id,
        command=request.command,
        args=request.args,
        cwd=cwd,
        risk_level=classification.risk_level,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr
    )
    
    # 7. Check if output is truncated
    MAX_OUTPUT = 100_000  # 100KB
    truncated = len(stdout) > MAX_OUTPUT or len(stderr) > MAX_OUTPUT
    
    return TerminalExecuteResponse(
        session_id=session.session_id,
        exit_code=exit_code,
        stdout=stdout[:MAX_OUTPUT] if truncated else stdout,
        stderr=stderr[:MAX_OUTPUT] if truncated else stderr,
        truncated=truncated,
        audit_hash=audit_hash,
        input_required=False
    )


@app.get("/tools/terminal:list_sessions", response_model=List[SessionInfo])
async def terminal_list_sessions():
    """List all active terminal sessions."""
    if not state.session_manager:
        raise HTTPException(status_code=503, detail="Adapter not initialized")
    
    sessions = state.session_manager.list_sessions()
    return [SessionInfo(**s) for s in sessions]


@app.post("/tools/terminal:write_input")
async def terminal_write_input(request: TerminalWriteInputRequest = Body(...)):
    """Write stdin to a running session."""
    # TODO: Implement interactive session management
    raise HTTPException(status_code=501, detail="Interactive sessions not yet implemented")


@app.post("/tools/terminal:anchor_session", response_model=TerminalAnchorResponse)
async def terminal_anchor_session(session_id: str):
    """Force anchor a session's Merkle root to the audit chain."""
    if not state.session_manager:
        raise HTTPException(status_code=503, detail="Adapter not initialized")
    
    session = state.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    merkle_root = await state.session_manager.anchor_session(session_id, immediate=True)
    
    return TerminalAnchorResponse(
        session_id=session_id,
        merkle_root=merkle_root or "",
        action_count=len(session.actions)
    )


@app.post("/tools/terminal:abort")
async def terminal_abort(session_id: str):
    """Abort a running command in a session."""
    # TODO: Implement session process tracking and SIGTERM
    raise HTTPException(status_code=501, detail="Session abort not yet implemented")


# ============================================================================
# Command Execution
# ============================================================================

async def _execute_command(
    command: str,
    args: List[str],
    cwd: str,
    env: Optional[Dict[str, str]],
    timeout_ms: int
) -> tuple[str, str, int]:
    """Execute a command in a sandboxed subprocess.
    
    Uses subprocess with strict environment controls.
    """
    # Build environment (inherit minimal, add overrides)
    safe_env = {
        "PATH": os.getenv("PATH", "/usr/bin:/bin"),
        "HOME": os.getenv("HOME", "/tmp"),
        "LANG": "en_US.UTF-8",
        "TERM": "xterm-256color",
    }
    if env:
        # Filter dangerous env vars
        dangerous = {"LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES"}
        for k, v in env.items():
            if k not in dangerous:
                safe_env[k] = v
    
    # Build command
    cmd = [command] + args
    
    # Execute
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=safe_env,
    )
    
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout_ms / 1000
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise
    
    return (
        stdout_bytes.decode("utf-8", errors="replace"),
        stderr_bytes.decode("utf-8", errors="replace"),
        proc.returncode or 0
    )


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8083))
    uvicorn.run(app, host="0.0.0.0", port=port)
