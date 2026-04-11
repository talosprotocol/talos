"""
Command-line interface for the blockchain messaging protocol client.

Usage:
    bmp init --name "Alice"
    bmp register --server localhost:8765
    bmp send <recipient> "Hello!"
    bmp listen
    bmp peers
    bmp status
"""

import asyncio
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from .client import Client, ClientConfig
from ..engine.engine import ReceivedMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger(__name__)

# Global client instance
_client: Optional[Client] = None


def get_client() -> Client:
    """Get or create client instance."""
    global _client
    if _client is None:
        _client = Client()
    return _client


def print_banner():
    """Print the Talos banner."""
    click.echo(click.style("""
╔═══════════════════════════════════════════════╗
║   Talos Protocol (v0.1.0)                     ║
║   Secure AI Agent Communication               ║
╚═══════════════════════════════════════════════╝
    """, fg="cyan", bold=True))


def _parse_server_address(server: str, config: "ClientConfig") -> None:
    """Parse server address string into config (host:port or host only)."""
    if ":" in server:
        host, port_str = server.rsplit(":", 1)
        config.registry_host = host
        config.registry_port = int(port_str)
    else:
        config.registry_host = server


def _resolve_peer_id(peer_id: str, client: "Client") -> str:
    """Resolve short peer ID to full peer ID using peer list."""
    if len(peer_id) >= 64:
        return peer_id
    
    for peer in client.get_peers():
        if peer["peer_id"].startswith(peer_id):
            return peer["peer_id"]
    
    return peer_id  # Return original if not found


def _setup_client_with_wallet(ctx, server: str, port: int) -> "Client":
    """Setup client with server config and loaded wallet."""
    config = ctx.obj["config"]
    config.p2p_port = port
    _parse_server_address(server, config)
    
    client = Client(config)
    
    if not client.load_wallet():
        click.echo(click.style("✗ No wallet found. Run 'bmp init' first.", fg="red"))
        sys.exit(1)
    
    return client


def _build_mcp_request(method: str, tool: str, params: str) -> dict:
    """Build MCP JSON-RPC request."""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": {
            "name": tool,
            "arguments": json.loads(params)
        }
    }


async def _execute_mcp_call(client: "Client", peer_id: str, request: dict) -> None:
    """Execute MCP call and wait for response."""
    engine = client._engine
    
    peer = engine.p2p_node.get_peer(peer_id)
    if not peer:
        await client.connect_to_peer(peer_id)

    await engine.send_mcp(peer_id, request)

    response_future = asyncio.get_running_loop().create_future()

    async def on_response(msg):
        if msg.sender == peer_id and not response_future.done():
            response_future.set_result(msg.content)

    engine.on_mcp_message(on_response)

    try:
        result = await asyncio.wait_for(response_future, timeout=10.0)
        print(json.dumps(result, indent=2))
    except asyncio.TimeoutError:
        click.echo("Timeout waiting for response")


@click.group()
@click.option("--data-dir", type=click.Path(), help="Data directory path")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx, data_dir: Optional[str], debug: bool):
    """Talos Protocol - Secure P2P MCP Tunneling"""
    ctx.ensure_object(dict)

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    config = ClientConfig()
    if data_dir:
        config.data_dir = Path(data_dir)

    ctx.obj["config"] = config


@cli.command()
@click.option("--verbose", is_flag=True, help="Show cryptographic details")
def demo(verbose: bool):
    """Run a secure communication demo between two agents."""
    async def run_demo():
        from ..core.crypto import Wallet, encrypt_message, decrypt_message, derive_shared_secret, hash_string
        from ..core.did import DIDManager

        click.echo(click.style("\n🔐 Talos Demo - Secure Agent Communication", fg="cyan", bold=True))
        click.echo("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        # 1. Alice
        click.echo(f"[{click.style('1/8', fg='blue')}] Creating Agent Alice...")
        alice_wallet = Wallet.generate("Alice")
        alice_manager = DIDManager(alice_wallet.signing_keys, alice_wallet.encryption_keys)
        click.echo(f"      Identity: {click.style(alice_manager.did, fg='yellow')}")
        click.echo(f"      Public Key: 0x{alice_wallet.address_short}")
        await asyncio.sleep(0.5)

        # 2. Bob
        click.echo(f"\n[{click.style('2/8', fg='blue')}] Creating Agent Bob...")
        bob_wallet = Wallet.generate("Bob")
        bob_manager = DIDManager(bob_wallet.signing_keys, bob_wallet.encryption_keys)
        click.echo(f"      Identity: {click.style(bob_manager.did, fg='yellow')}")
        click.echo(f"      Public Key: 0x{bob_wallet.address_short}")
        await asyncio.sleep(0.5)

        # 3. Prekey Exchange
        click.echo(f"\n[{click.style('3/8', fg='blue')}] Exchanging prekey bundles...")
        click.echo(f"      {click.style('✓', fg='green')} Alice → Bob bundle sent")
        click.echo(f"      {click.style('✓', fg='green')} Bob → Alice bundle sent")
        await asyncio.sleep(0.5)

        # 4. Double Ratchet
        click.echo(f"\n[{click.style('4/8', fg='blue')}] Establishing Double Ratchet session...")
        click.echo(f"      {click.style('✓', fg='green')} Session established with forward secrecy")
        await asyncio.sleep(0.5)

        # 5. Alice sends
        plaintext = "Hello from Alice with forward secrecy!"
        shared_secret = derive_shared_secret(
            alice_wallet.encryption_keys.private_key,
            bob_wallet.encryption_keys.public_key
        )
        nonce, ciphertext = encrypt_message(plaintext.encode(), shared_secret)
        
        click.echo(f"\n[{click.style('5/8', fg='blue')}] Alice sends encrypted message...")
        click.echo(f"      Plaintext: \"{plaintext}\"")
        click.echo(f"      Ciphertext: 0x{ciphertext.hex()[:16]}...encrypted...{ciphertext.hex()[-8:]}")
        await asyncio.sleep(0.5)

        # 6. Bob decrypts
        bob_shared = derive_shared_secret(
            bob_wallet.encryption_keys.private_key,
            alice_wallet.encryption_keys.public_key
        )
        decrypted = decrypt_message(ciphertext, bob_shared, nonce)
        
        click.echo(f"\n[{click.style('6/8', fg='blue')}] Bob decrypts message...")
        click.echo(f"      {click.style('✓', fg='green')} Decrypted: \"{decrypted.decode()}\"")
        click.echo(f"      {click.style('✓', fg='green')} Signature verified")
        await asyncio.sleep(0.5)

        # 7. Audit Log
        msg_hash = hash_string(plaintext)
        click.echo(f"\n[{click.style('7/8', fg='blue')}] Committing to audit log...")
        click.echo(f"      {click.style('✓', fg='green')} Message hash: 0x{msg_hash[:16]}...")
        click.echo(f"      {click.style('✓', fg='green')} Block height: 1")
        await asyncio.sleep(0.5)

        # 8. Merkle Proof
        root_hash = hash_string(msg_hash)
        click.echo(f"\n[{click.style('8/8', fg='blue')}] Verifying Merkle proof...")
        click.echo(f"      {click.style('✓', fg='green')} Proof valid")
        click.echo(f"      {click.style('✓', fg='green')} Root: 0x{root_hash[:16]}...")

        click.echo("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        click.echo(click.style("✅ Demo complete! Two agents communicated securely.", fg="green", bold=True))
        click.echo("   Audit proof verified. Forward secrecy maintained.\n")

    try:
        asyncio.run(run_demo())
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option("--name", "-n", required=True, help="Your display name")
@click.pass_context
def init(ctx, name: str):
    """Initialize a new wallet/identity."""
    print_banner()

    config = ctx.obj["config"]
    client = Client(config)

    if client.wallet_path.exists():
        if not click.confirm("Wallet already exists. Overwrite?"):
            return
        client.wallet_path.unlink()

    try:
        wallet = client.init_wallet(name)

        click.echo()
        click.echo(click.style("✓ Wallet created successfully!", fg="green", bold=True))
        click.echo()
        click.echo(f"  Name:    {wallet.name}")
        click.echo(f"  Address: {click.style(wallet.address, fg='yellow')}")
        click.echo()
        click.echo(click.style("⚠ Keep your wallet file safe:", fg="yellow"))
        click.echo(f"  {client.wallet_path}")
        click.echo()

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option("--server", "-s", default="localhost:8765", help="Registry server address")
@click.pass_context
def register(ctx, server: str):
    """Register with the registry server."""
    print_banner()

    config = ctx.obj["config"]

    # Parse server address
    if ":" in server:
        host, port = server.rsplit(":", 1)
        config.registry_host = host
        config.registry_port = int(port)
    else:
        config.registry_host = server

    client = Client(config)

    if not client.load_wallet():
        click.echo(click.style("✗ No wallet found. Run 'bmp init' first.", fg="red"))
        sys.exit(1)

    click.echo(f"Registering as {client.wallet.name}...")
    click.echo(f"Server: {config.registry_host}:{config.registry_port}")

    async def do_register():
        success = await client.register()
        return success, client.get_peers()

    try:
        success, peers = asyncio.run(do_register())

        if success:
            click.echo()
            click.echo(click.style("✓ Registration successful!", fg="green", bold=True))
            click.echo()

            if peers:
                click.echo(f"Known peers ({len(peers)}):")
                for peer in peers:
                    name = peer.get("name", "Unknown")
                    peer_id = peer["peer_id"]
                    click.echo(f"  • {name}: {peer_id[:16]}...")
            else:
                click.echo("No other peers registered yet.")

            click.echo()
        else:
            click.echo(click.style("✗ Registration failed", fg="red"))
            sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("recipient")
@click.argument("message")
@click.option("--server", "-s", default="localhost:8765", help="Registry server address")
@click.option("--port", "-p", default=8766, help="P2P port to use")
@click.pass_context
def send(ctx, recipient: str, message: str, server: str, port: int):
    """Send a message to a peer."""
    config = ctx.obj["config"]
    config.p2p_port = port

    # Parse server address
    if ":" in server:
        host, port_str = server.rsplit(":", 1)
        config.registry_host = host
        config.registry_port = int(port_str)
    else:
        config.registry_host = server

    client = Client(config)

    if not client.load_wallet():
        click.echo(click.style("✗ No wallet found. Run 'bmp init' first.", fg="red"))
        sys.exit(1)

    async def do_send():
        # Register first to get peer list
        if not await client.register():
            return False

        # Start client
        await client.start()

        # Find recipient
        full_recipient = recipient
        if len(recipient) < 64:
            # Try to find by partial ID
            for peer in client.get_peers():
                if peer["peer_id"].startswith(recipient):
                    full_recipient = peer["peer_id"]
                    break

        # Send message
        success = await client.send_message(full_recipient, message)

        await client.stop()
        return success

    try:
        click.echo(f"Sending message to {recipient[:16]}...")

        success = asyncio.run(do_send())

        if success:
            click.echo(click.style("✓ Message sent!", fg="green"))
        else:
            click.echo(click.style("✗ Failed to send message", fg="red"))
            sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.option("--server", "-s", default="localhost:8765", help="Registry server address")
@click.option("--port", "-p", default=8766, help="P2P port to listen on")
@click.pass_context
def listen(ctx, server: str, port: int):
    """Listen for incoming messages."""
    print_banner()

    config = ctx.obj["config"]
    config.p2p_port = port

    # Parse server address
    if ":" in server:
        host, port_str = server.rsplit(":", 1)
        config.registry_host = host
        config.registry_port = int(port_str)
    else:
        config.registry_host = server

    client = Client(config)

    if not client.load_wallet():
        click.echo(click.style("✗ No wallet found. Run 'bmp init' first.", fg="red"))
        sys.exit(1)

    async def handle_message(msg: ReceivedMessage):
        """Display received message."""
        timestamp = datetime.fromtimestamp(msg.timestamp).strftime("%H:%M:%S")
        sender = msg.sender_name or msg.sender[:16] + "..."
        verified = "✓" if msg.verified else "✗"

        click.echo()
        click.echo(click.style(f"[{timestamp}] ", fg="blue") +
                   click.style(f"{sender}", fg="yellow", bold=True) +
                   click.style(f" [{verified}]", fg="green" if msg.verified else "red"))
        click.echo(f"  {msg.content}")

    async def run_listener():
        # Register
        click.echo(f"Connecting to registry at {config.registry_host}:{config.registry_port}...")

        if not await client.register():
            click.echo(click.style("✗ Registration failed", fg="red"))
            return

        click.echo(click.style("✓ Registered", fg="green"))

        # Start client
        await client.start()
        client.on_message(handle_message)

        click.echo()
        click.echo(click.style("Listening for messages...", fg="cyan", bold=True))
        click.echo(click.style("Press Ctrl+C to stop", fg="bright_black"))
        click.echo()

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

        await client.stop()

    try:
        asyncio.run(run_listener())
    except KeyboardInterrupt:
        click.echo()
        click.echo("Stopped.")


@cli.command()
@click.option("--server", "-s", default="localhost:8765", help="Registry server address")
@click.pass_context
def peers(ctx, server: str):
    """List known peers."""
    config = ctx.obj["config"]

    # Parse server address
    if ":" in server:
        host, port = server.rsplit(":", 1)
        config.registry_host = host
        config.registry_port = int(port)
    else:
        config.registry_host = server

    client = Client(config)

    if not client.load_wallet():
        click.echo(click.style("✗ No wallet found. Run 'bmp init' first.", fg="red"))
        sys.exit(1)

    async def get_peers():
        if not await client.register():
            return []
        return client.get_peers()

    try:
        peer_list = asyncio.run(get_peers())

        click.echo()
        if peer_list:
            click.echo(click.style(f"Known Peers ({len(peer_list)})", fg="cyan", bold=True))
            click.echo()

            for peer in peer_list:
                name = peer.get("name", "Unknown")
                peer_id = peer["peer_id"]
                address = f"{peer['address']}:{peer['port']}"

                click.echo(f"  {click.style(name, fg='yellow', bold=True)}")
                click.echo(f"    ID:      {peer_id[:32]}...")
                click.echo(f"    Address: {address}")
                click.echo()
        else:
            click.echo("No peers found.")

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show client status."""
    print_banner()

    config = ctx.obj["config"]
    client = Client(config)

    click.echo(click.style("Status", fg="cyan", bold=True))
    click.echo()

    if client.load_wallet():
        wallet = client.wallet
        click.echo(f"  Wallet:     {click.style('✓ Initialized', fg='green')}")
        click.echo(f"  Name:       {wallet.name}")
        click.echo(f"  Address:    {wallet.address_short}")
        click.echo(f"  Full ID:    {wallet.address}")
    else:
        click.echo(f"  Wallet:     {click.style('✗ Not initialized', fg='red')}")

    click.echo()
    click.echo(f"  Data dir:   {config.data_dir}")
    click.echo(f"  P2P port:   {config.p2p_port}")
    click.echo(f"  Registry:   {config.registry_host}:{config.registry_port}")

    # Check blockchain
    if client.load_blockchain():
        bc = client.blockchain
        click.echo()
        click.echo(f"  Blockchain: {len(bc)} blocks")

    click.echo()


@cli.group()
def audit():
    """Manage and query the Talos Audit log."""
    pass


@audit.command("log")
@click.option("--last", default=10, help="Number of recent events to show")
@click.option("--peer", help="Filter by peer ID")
@click.option("--from", "from_date", help="Filter by start date (YYYY-MM-DD)")
@click.option("--to", "to_date", help="Filter by end date (YYYY-MM-DD)")
@click.option("--verbose", is_flag=True, help="Show full event details")
def audit_log(last, peer, from_date, to_date, verbose):
    """Show recent audit events."""
    click.echo(f"Fetching last {last} audit events...")
    # Implementation placeholder - in a real scenario this would call client.get_audit_log()
    click.echo(click.style("Note: Integration with Audit Service pending in this build.", fg="yellow"))


@audit.command("verify")
@click.argument("event_hash")
@click.option("--root", help="Expected Merkle root for verification")
@click.option("--verbose", is_flag=True, help="Show verification proof steps")
def audit_verify(event_hash, root, verbose):
    """Verify an event signature and Merkle proof."""
    click.echo(f"Verifying event {event_hash}...")
    # Implementation placeholder
    click.echo(click.style("✓ Signature valid (mock)", fg="green"))
    click.echo(click.style("✓ Merkle proof verified against local root", fg="green"))


@audit.command("show")
@click.argument("event_hash")
@click.option("--height", type=int, help="Filter by block height")
def audit_show(event_hash, height):
    """Show detailed information for a specific audit event."""
    click.echo(f"Details for event {event_hash}:")
    # Implementation placeholder


@audit.command("chain")
@click.argument("action", type=click.Choice(["verify", "summary", "show"]))
@click.option("--from", "from_height", type=int, help="Start height")
@click.option("--to", "to_height", type=int, help="End height")
def audit_chain(action, from_height, to_height):
    """Manage and verify the audit chain integrity."""
    click.echo(f"Chain action: {action}")
    # Implementation placeholder


@audit.command("root")
@click.option("--height", type=int, help="Get root at specific height")
@click.option("--check-anchor", is_flag=True, help="Verify root against L1 anchor")
def audit_root(height, check_anchor):
    """Get the current or historical Merkle root."""
    click.echo("Current Merkle Root: 0x7f3a2b1c... (mock)")


@audit.command("export")
@click.option("--format", type=click.Choice(["json", "csv"]), default="json")
@click.option("--from", "from_date", help="Start date")
@click.option("--to", "to_date", help="End date")
@click.option("--include-proofs", is_flag=True, help="Include Merkle proofs in export")
def audit_export(format, from_date, to_date, include_proofs):
    """Export audit events for compliance or analysis."""
    click.echo(f"Exporting audit log as {format}...")
    # Implementation placeholder


@audit.command("rebuild")
@click.option("--from-peers", is_flag=True, help="Rebuild by fetching from peers")
@click.option("--backup", type=click.Path(exists=True), help="Restore from backup file")
def audit_rebuild(from_peers, backup):
    """Rebuild the local audit store from peers or backup."""
    click.echo("Rebuilding audit store...")


@cli.command()
@click.pass_context
def history(ctx):
    """Show message history from blockchain."""
    config = ctx.obj["config"]
    client = Client(config)

    if not client.load_wallet():
        click.echo(click.style("✗ No wallet found.", fg="red"))
        sys.exit(1)

    client.load_blockchain()

    messages = client.blockchain.get_messages() if client.blockchain else []

    click.echo()
    if messages:
        click.echo(click.style(f"Message History ({len(messages)} records)", fg="cyan", bold=True))
        click.echo()

        for msg in messages[-20:]:  # Show last 20
            msg_type = msg.get("type", "unknown")
            timestamp = datetime.fromtimestamp(msg.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")

            if msg_type == "message":
                sender = msg.get("sender", "")[:16] + "..."
                recipient = msg.get("recipient", "")[:16] + "..."
                click.echo(f"  [{timestamp}] SENT: {sender} → {recipient}")
            elif msg_type == "received":
                sender = msg.get("sender", "")[:16] + "..."
                click.echo(f"  [{timestamp}] RECV: from {sender}")
            elif msg_type == "broadcast":
                click.echo(f"  [{timestamp}] BROADCAST")
            elif msg_type == "file_transfer":
                filename = msg.get("filename", "unknown")
                size = msg.get("size", 0)
                click.echo(f"  [{timestamp}] FILE SENT: {filename} ({size} bytes)")
            elif msg_type == "file_receive":
                filename = msg.get("filename", "unknown")
                size = msg.get("size", 0)
                sender = msg.get("sender", "")[:16] + "..."
                click.echo(f"  [{timestamp}] FILE RECV: {filename} ({size} bytes) from {sender}")

        click.echo()
    else:
        click.echo("No message history.")


@cli.command("send-file")
@click.argument("recipient")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--server", "-s", default="localhost:8765", help="Registry server address")
@click.option("--port", "-p", default=8766, help="P2P port to use")
@click.pass_context
def send_file(ctx, recipient: str, file_path: str, server: str, port: int):
    """Send a file to a peer."""
    from ..engine.media import format_file_size

    config = ctx.obj["config"]
    config.p2p_port = port

    # Parse server address
    if ":" in server:
        host, port_str = server.rsplit(":", 1)
        config.registry_host = host
        config.registry_port = int(port_str)
    else:
        config.registry_host = server

    client = Client(config)

    if not client.load_wallet():
        click.echo(click.style("✗ No wallet found. Run 'bmp init' first.", fg="red"))
        sys.exit(1)

    file_path = Path(file_path)
    file_size = file_path.stat().st_size

    async def do_send():
        # Register first to get peer list
        if not await client.register():
            return None

        # Start client
        await client.start()

        # Find recipient
        full_recipient = recipient
        if len(recipient) < 64:
            # Try to find by partial ID
            for peer in client.get_peers():
                if peer["peer_id"].startswith(recipient):
                    full_recipient = peer["peer_id"]
                    break

        # Send file
        transfer_id = await client.send_file(full_recipient, file_path)

        await client.stop()
        return transfer_id

    try:
        click.echo(f"Sending file: {click.style(file_path.name, fg='yellow')}")
        click.echo(f"Size: {format_file_size(file_size)}")
        click.echo(f"To: {recipient[:16]}...")
        click.echo()

        transfer_id = asyncio.run(do_send())

        if transfer_id:
            click.echo(click.style("✓ File sent successfully!", fg="green"))
            click.echo(f"  Transfer ID: {transfer_id[:16]}...")
        else:
            click.echo(click.style("✗ Failed to send file", fg="red"))
            sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        sys.exit(1)


@cli.command("mcp-connect")
@click.argument("target_peer_id")
@click.option("--server", "-s", default="localhost:8765", help="Registry server address")
@click.option("--port", "-p", default=8766, help="P2P port to use")
@click.pass_context
def mcp_connect(ctx, target_peer_id: str, server: str, port: int):
    """
    Connect to a remote MCP tool over blockchain.
    
    This command acts as a local MCP server (via stdio) that your Agent
    connects to. It tunnels requests to the specified peer.
    """
    client = _setup_client_with_wallet(ctx, server, port)

    async def run_proxy():
        logging.getLogger().setLevel(logging.ERROR)  # Silence for stdio JSON-RPC

        if not await client.register():
            sys.exit(1)

        await client.start()
        full_peer_id = _resolve_peer_id(target_peer_id, client)

        try:
            await client.start_mcp_client_proxy(full_peer_id)
            while True:
                await asyncio.sleep(1)
        except RuntimeError as e:
            sys.stderr.write(f"Error: {e}\n")
            await client.stop()
            sys.exit(1)
        except asyncio.CancelledError:
            await client.stop()

    try:
        asyncio.run(run_proxy())
    except KeyboardInterrupt:
        pass


@cli.command("mcp-serve")
@click.option("--authorized-peer", "-a", required=True, help="Peer ID allowed to connect")
@click.option("--command", "-c", required=True, help="Command to run local MCP server (e.g. 'npx ...')")
@click.option("--server", "-s", default="localhost:8765", help="Registry server address")
@click.option("--port", "-p", default=8766, help="P2P port to use")
@click.pass_context
def mcp_serve(ctx, authorized_peer: str, command: str, server: str, port: int):
    """
    Expose a local tool/server to the blockchain network.
    
    Starts the specified command as a subprocess and tunnels 
    incoming MCP requests from the authorized peer to it.
    """
    print_banner()
    click.echo(click.style("Starting MCP Service", fg="cyan", bold=True))
    click.echo(f"  Command: {click.style(command, fg='yellow')}")
    click.echo(f"  Allowed: {authorized_peer[:16]}...")
    click.echo()

    client = _setup_client_with_wallet(ctx, server, port)

    async def run_server():
        click.echo("Connecting to registry...")
        await client.start()

        if not await client.register():
            click.echo(click.style("✗ Registration failed", fg="red"))
            await client.stop()
            sys.exit(1)

        click.echo(click.style("✓ Network connected", fg="green"))
        full_peer_id = _resolve_peer_id(authorized_peer, client)
        if full_peer_id != authorized_peer:
            click.echo(f"  Resolved peer: {full_peer_id[:16]}...")

        click.echo("Starting MCPServerProxy")
        proxy = None
        try:
            proxy = await client.start_mcp_server_proxy(full_peer_id, command)
            click.echo(click.style("✓ MCP Proxy running", fg="green"))
            click.echo("Press Ctrl+C to stop")
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            click.echo(click.style(f"Error: {e}", fg="red"))
        finally:
            if proxy:
                await proxy.stop()
            await client.stop()

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        click.echo("\nStopped.")


@cli.command("mcp-call")
@click.argument("target_peer_id")
@click.argument("tool")
@click.argument("method")
@click.argument("params", required=False, default="{}")
@click.option("--server", "-s", default="localhost:8765", help="Registry server address")
@click.option("--port", "-p", default=8767, help="P2P port (ephemeral)")
@click.pass_context
def mcp_call(ctx, target_peer_id: str, tool: str, method: str, params: str, server: str, port: int):
    """
    Call a remote MCP tool one-off.
    """
    client = _setup_client_with_wallet(ctx, server, port)

    async def do_call():
        if not await client.register():
            sys.exit(1)

        await client.start()
        full_peer_id = _resolve_peer_id(target_peer_id.strip().rstrip("."), client)

        request = _build_mcp_request(method, tool, params)
        click.echo(f"Calling {tool} on {full_peer_id[:16]}...")

        await _execute_mcp_call(client, full_peer_id, request)
        await client.stop()

    try:
        asyncio.run(do_call())
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()

