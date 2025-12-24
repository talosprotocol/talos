import asyncio
import sys
import json
import logging
import shlex
from typing import Optional, Any

from ..engine.engine import TransmissionEngine, MCPMessage

logger = logging.getLogger(__name__)

class MCPProxyBase:
    """Base class for MCP proxies."""
    
    def __init__(self, engine: TransmissionEngine, peer_id: str):
        self.engine = engine
        self.peer_id = peer_id
        self.running = False
        
        # Register callback
        self.engine.on_mcp_message(self.handle_bmp_message)

    async def start(self):
        self.running = True
        logger.info(f"Starting {self.__class__.__name__}")
        
    async def stop(self):
        self.running = False
        logger.info(f"Stopping {self.__class__.__name__}")

    async def handle_bmp_message(self, message: MCPMessage):
        """Handle incoming message from BMP network."""
        pass


class MCPClientProxy(MCPProxyBase):
    """
    Client-side proxy (running on the Agent's machine).
    
    Acts as an MCP Server to the local Agent (via stdio), 
    but forwards everything to a remote peer.
    """
    
    async def start(self):
        await super().start()
        # Start reading from stdin
        asyncio.create_task(self._read_stdin())
        
    async def _read_stdin(self):
        """Read JSON-RPC messages from stdin and forward to peer."""
        if not hasattr(self, 'reader') or self.reader is None:
            loop = asyncio.get_event_loop()
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            await loop.connect_read_pipe(lambda: protocol, sys.stdin)
            self.reader = reader
        
        while self.running:
            try:
                line = await self.reader.readline()
                if not line:
                    break
                    
                # Parse JSON to ensure validity before sending
                try:
                    data = json.loads(line)
                    logger.debug(f"Client -> BMP: {data.get('method', 'response')}")
                    
                    # Send to remote peer
                    await self.engine.send_mcp(self.peer_id, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from stdin: {line}")
                    
            except Exception as e:
                logger.error(f"Error reading stdin: {e}")
                break

    async def handle_bmp_message(self, message: MCPMessage):
        """Handle response from remote peer, write to stdout."""
        if message.sender != self.peer_id:
            return
            
        logger.debug(f"BMP -> Client: {message.content.get('method', 'response')}")
        
        # Write to stdout for the Agent to read
        print(json.dumps(message.content), flush=True)


class MCPServerProxy(MCPProxyBase):
    """
    Server-side proxy (running on the Tool's machine).
    
    Spawns the actual MCP server as a subprocess and bridges
    BMP messages to it.
    
    Features:
    - Access control via ACLManager
    - Per-tool and per-resource permissions
    - Rate limiting
    - Audit logging
    """
    
    def __init__(
        self,
        engine: TransmissionEngine,
        allowed_client_id: str,
        command: str,
        acl_manager: Optional[Any] = None,
    ):
        super().__init__(engine, allowed_client_id)
        self.command = command
        self.process: Optional[asyncio.subprocess.Process] = None
        self.acl_manager = acl_manager  # Optional ACLManager for fine-grained control
        
    async def start(self):
        await super().start()
        
        # Spawn subprocess
        args = shlex.split(self.command)
        self.process = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        logger.info(f"Spawned MCP server: {self.command}")
        
        # Start reading from subprocess
        asyncio.create_task(self._read_subprocess_stdout())
        asyncio.create_task(self._read_subprocess_stderr())

    async def stop(self):
        await super().stop()
        if self.process:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception:
                pass

    async def handle_bmp_message(self, message: MCPMessage):
        """Handle request from remote client, write to subprocess stdin."""
        if message.sender != self.peer_id:
            logger.warning(f"Rejected MCP message from unauthorized peer: {message.sender}")
            return
        
        content = message.content
        method = content.get("method", "")
        params = content.get("params", {})
        
        # ACL Check (if manager is configured)
        if self.acl_manager:
            result = self.acl_manager.check(message.sender, method, params)
            if not result.allowed:
                logger.warning(f"ACL denied: {result.reason}")
                # Send error response back to client
                error_response = {
                    "jsonrpc": "2.0",
                    "id": content.get("id"),
                    "error": {
                        "code": -32600,
                        "message": f"Access denied: {result.reason}",
                        "data": {"permission": result.permission.name},
                    }
                }
                await self.engine.send_mcp(self.peer_id, error_response, is_response=True)
                return
            
        logger.debug(f"BMP -> Server: {method or 'response'}")
        
        if self.process and self.process.stdin:
            # Write to subprocess stdin
            payload = json.dumps(content) + "\n"
            self.process.stdin.write(payload.encode())
            await self.process.stdin.drain()

    async def _read_subprocess_stdout(self):
        """Read output from MCP server and forward to client."""
        if not self.process or not self.process.stdout:
            return
            
        while self.running:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                    
                try:
                    data = json.loads(line)
                    logger.debug(f"Server -> BMP: {data.get('method', 'response')}")
                    
                    # Send back to client
                    await self.engine.send_mcp(self.peer_id, data, is_response=True)
                except json.JSONDecodeError:
                    # Not JSON, maybe just logs?
                    logger.debug(f"Server stdout (non-JSON): {line.decode().strip()}")
                    
            except Exception as e:
                logger.error(f"Error reading server stdout: {e}")
                break

    async def _read_subprocess_stderr(self):
        """Log stderr from MCP server."""
        if not self.process or not self.process.stderr:
            return
            
        while self.running:
            line = await self.process.stderr.readline()
            if not line:
                break
            logger.warning(f"MCP Server Stderr: {line.decode().strip()}")
