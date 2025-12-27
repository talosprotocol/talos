"""
Main server entry point for the blockchain messaging protocol.

This module provides:
- CLI for running the registry server
- Combined registry + P2P node functionality
"""

import argparse
import asyncio
import logging
import signal

from ..core.crypto import Wallet
from .registry import RegistryServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


class TalosServer:
    """
    Main server combining registry and P2P functionality.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        name: str = "TalosServer"
    ) -> None:
        """
        Initialize Talos server.
        
        Args:
            host: Host address to bind
            port: Port to listen on
            name: Server name
        """
        self.host = host
        self.port = port
        self.name = name

        # Generate server identity
        self.wallet = Wallet.generate(name)

        # Components
        self.registry_server = RegistryServer(
            host=host,
            port=port,
            wallet=self.wallet
        )

        self._running = False

    async def start(self) -> None:
        """Start the server."""
        if self._running:
            return

        self._running = True

        logger.info("=" * 50)
        logger.info("Talos Protocol Server")
        logger.info("=" * 50)
        logger.info(f"Server Name: {self.name}")
        logger.info(f"Address: {self.wallet.address_short}")
        logger.info(f"Listening on: {self.host}:{self.port}")
        logger.info("=" * 50)

        await self.registry_server.start()

    async def stop(self) -> None:
        """Stop the server."""
        if not self._running:
            return

        self._running = False

        await self.registry_server.stop()

        logger.info("Server stopped")

    async def run_forever(self) -> None:
        """Run server until interrupted."""
        await self.start()

        # Set up signal handlers
        loop = asyncio.get_running_loop()

        stop_event = asyncio.Event()

        def handle_signal():
            logger.info("Received shutdown signal...")
            stop_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_signal)

        # Wait for shutdown
        await stop_event.wait()
        await self.stop()


def main():
    """CLI entry point for the server."""
    parser = argparse.ArgumentParser(
        description="Talos Protocol Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host address to bind"
    )

    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8765,
        help="Port to listen on"
    )

    parser.add_argument(
        "--name", "-n",
        default="TalosServer",
        help="Server name"
    )

    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    server = TalosServer(
        host=args.host,
        port=args.port,
        name=args.name
    )

    try:
        asyncio.run(server.run_forever())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
