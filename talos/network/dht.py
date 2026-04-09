"""
LEGACY Kademlia Distributed Hash Table (DHT) Implementation.

This module is part of the legacy P2P stack and is scheduled for removal.
New services should use the libp2p-based gateway for discovery and storage.

Usage:
    from talos.network.dht import DHTNode, NodeInfo
    
    # Create DHT node
    node = DHTNode(node_id, host, port)
    
    # Join network via bootstrap
    await node.bootstrap(bootstrap_nodes)
    
    # Store DID document
    await node.store(did, document)
    
    # Lookup DID
    document = await node.get(did)
"""

import asyncio
import hashlib
import json
import logging
import time
from pydantic import BaseModel, Field, ConfigDict
from typing import Any, Optional, Callable

logger = logging.getLogger(__name__)

# Kademlia parameters
K = 20  # Bucket size (max contacts per bucket)
ALPHA = 3  # Parallelism factor for lookups
ID_BITS = 256  # Node ID size in bits


class NodeInfo(BaseModel):
    """Information about a DHT node."""

    node_id: str  # 256-bit hex ID
    host: str
    port: int
    last_seen: float = Field(default_factory=time.time)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def address(self) -> tuple[str, int]:
        return (self.host, self.port)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NodeInfo":
        return cls(
            node_id=data["node_id"],
            host=data["host"],
            port=data["port"],
            last_seen=data.get("last_seen", 0),
        )

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, NodeInfo):
            return self.node_id == other.node_id
        return False


def xor_distance(id1: str, id2: str) -> int:
    """
    Calculate XOR distance between two node IDs.
    
    Args:
        id1: First node ID (hex string)
        id2: Second node ID (hex string)
        
    Returns:
        Integer XOR distance
    """
    return int(id1, 16) ^ int(id2, 16)


def bucket_index(node_id: str, target_id: str) -> int:
    """
    Get the bucket index for a target ID.
    
    Returns the position of the highest differing bit.
    """
    distance = xor_distance(node_id, target_id)
    if distance == 0:
        return 0
    return distance.bit_length() - 1


def generate_node_id(data: Optional[bytes] = None) -> str:
    """
    Generate a random node ID.
    
    Args:
        data: Optional seed data
        
    Returns:
        256-bit hex node ID
    """
    import os
    if data is None:
        data = os.urandom(32)
    return hashlib.sha256(data).hexdigest()


class RoutingTable:
    """
    Kademlia routing table with k-buckets.
    
    Organizes contacts by XOR distance from local node.
    """

    def __init__(self, local_id: str, k: int = K):
        """
        Initialize routing table.
        
        Args:
            local_id: This node's ID
            k: Maximum contacts per bucket
        """
        self.local_id = local_id
        self.k = k

        # K-buckets indexed by distance prefix length
        self.buckets: list[list[NodeInfo]] = [[] for _ in range(ID_BITS)]

    def add_contact(self, node: NodeInfo) -> bool:
        """
        Add or update a contact in the routing table.
        
        Args:
            node: Node to add
            
        Returns:
            True if added, False if bucket full
        """
        if node.node_id == self.local_id:
            return False

        index = bucket_index(self.local_id, node.node_id)
        bucket = self.buckets[index]

        # Check if already exists
        for i, existing in enumerate(bucket):
            if existing.node_id == node.node_id:
                # Move to end (most recently seen)
                bucket.pop(i)
                node.last_seen = time.time()
                bucket.append(node)
                return True

        # Add to bucket if space
        if len(bucket) < self.k:
            node.last_seen = time.time()
            bucket.append(node)
            return True

        # Bucket full - could ping oldest and replace if unresponsive
        return False

    def remove_contact(self, node_id: str) -> bool:
        """Remove a contact from the routing table."""
        index = bucket_index(self.local_id, node_id)
        bucket = self.buckets[index]

        for i, node in enumerate(bucket):
            if node.node_id == node_id:
                bucket.pop(i)
                return True
        return False

    def get_closest(self, target_id: str, count: int = K) -> list[NodeInfo]:
        """
        Get the closest contacts to a target ID.
        
        Args:
            target_id: ID to find closest contacts to
            count: Maximum contacts to return
            
        Returns:
            List of closest contacts, sorted by distance
        """
        all_contacts: list[NodeInfo] = []

        for bucket in self.buckets:
            all_contacts.extend(bucket)

        # Sort by XOR distance to target
        all_contacts.sort(key=lambda n: xor_distance(n.node_id, target_id))

        return all_contacts[:count]

    def get_contact(self, node_id: str) -> Optional[NodeInfo]:
        """Get a specific contact by ID."""
        index = bucket_index(self.local_id, node_id)
        bucket = self.buckets[index]

        for node in bucket:
            if node.node_id == node_id:
                return node
        return None

    def contact_count(self) -> int:
        """Get total number of contacts."""
        return sum(len(bucket) for bucket in self.buckets)

    def to_dict(self) -> dict[str, Any]:
        """Serialize routing table."""
        return {
            "local_id": self.local_id,
            "k": self.k,
            "contacts": [
                node.to_dict()
                for bucket in self.buckets
                for node in bucket
            ],
        }


class DHTStorage:
    """
    Local storage for DHT key-value pairs.
    
    Stores DID documents and other data.
    """

    def __init__(self, max_age: float = 86400):
        """
        Initialize storage.
        
        Args:
            max_age: Maximum age for stored values (seconds)
        """
        self.max_age = max_age
        self._data: dict[str, tuple[Any, float]] = {}  # key -> (value, timestamp)

    def store(self, key: str, value: Any) -> None:
        """Store a value."""
        self._data[key] = (value, time.time())

    def get(self, key: str) -> Optional[Any]:
        """Get a value, returning None if expired or missing."""
        if key not in self._data:
            return None

        value, timestamp = self._data[key]

        # Check expiry
        if time.time() - timestamp > self.max_age:
            del self._data[key]
            return None

        return value

    def delete(self, key: str) -> bool:
        """Delete a value."""
        if key in self._data:
            del self._data[key]
            return True
        return False

    def cleanup(self) -> int:
        """Remove expired entries."""
        now = time.time()
        expired = [k for k, (_, t) in self._data.items() if now - t > self.max_age]
        for key in expired:
            del self._data[key]
        return len(expired)

    def __len__(self) -> int:
        return len(self._data)


class DHTNode:
    """
    Kademlia DHT node implementation.
    
    Provides distributed storage and lookup for DID documents.
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        host: str = "0.0.0.0",
        port: int = 8468,
    ):
        """
        Initialize DHT node.
        
        Args:
            node_id: Optional node ID (generated if not provided)
            host: Listen host
            port: Listen port
        """
        self.node_id = node_id or generate_node_id()
        self.host = host
        self.port = port

        self.routing_table = RoutingTable(self.node_id)
        self.storage = DHTStorage()

        self._running = False
        self._protocol: Optional[DHTProtocol] = None
        self._pending_requests: dict[str, asyncio.Future] = {}

        # RPC handlers
        self._rpc_handlers: dict[str, Callable] = {
            "ping": self._handle_ping,
            "find_node": self._handle_find_node,
            "find_value": self._handle_find_value,
            "store": self._handle_store,
        }

    @property
    def node_info(self) -> NodeInfo:
        """Get this node's info."""
        return NodeInfo(
            node_id=self.node_id,
            host=self.host,
            port=self.port,
        )

    async def start(self) -> None:
        """Start the DHT node."""
        if self._running:
            return

        self._running = True

        # Start UDP server for DHT messages
        loop = asyncio.get_event_loop()

        # Create protocol
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: DHTProtocol(self),
            local_addr=(self.host, self.port),
        )
        self._protocol = protocol

        logger.info(f"DHT node started: {self.node_id[:16]}... on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the DHT node."""
        self._running = False
        logger.info("DHT node stopped")

    async def call_rpc(self, node: NodeInfo, rpc_type: str, data: dict) -> Optional[dict]:
        """
        Send an RPC request to a remote node.
        
        Args:
            node: Target node
            rpc_type: RPC method name
            data: RPC parameters
            
        Returns:
            RPC response data or None if failed/timed out
        """
        if not self._protocol:
            # If not started, try to use a temporary protocol or fail
            return None

        import uuid
        request_id = str(uuid.uuid4())
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        message = {
            "request_id": request_id,
            "sender_id": self.node_id,
            "type": rpc_type,
            "data": data,
        }

        try:
            self._protocol.send_message(message, node.address)
            # Wait for response with timeout
            return await asyncio.wait_for(future, timeout=2.0)
        except asyncio.TimeoutError:
            logger.debug(f"RPC {rpc_type} to {node.node_id[:8]} timed out")
            return None
        except Exception as e:
            logger.error(f"RPC {rpc_type} to {node.node_id[:8]} failed: {e}")
            return None
        finally:
            self._pending_requests.pop(request_id, None)

    async def bootstrap(self, nodes: list[NodeInfo]) -> int:
        """
        Bootstrap into the network.
        
        Args:
            nodes: Known bootstrap nodes
            
        Returns:
            Number of contacts added
        """
        added = 0

        for node in nodes:
            # Ping bootstrap node to verify and add to routing table
            response = await self.call_rpc(node, "ping", {})
            if response:
                self.routing_table.add_contact(node)
                added += 1

        # Lookup our own ID to populate routing table
        if added > 0:
            await self.lookup_node(self.node_id)

        logger.info(f"Bootstrapped with {added} nodes")
        return added

    async def lookup_node(self, target_id: str) -> list[NodeInfo]:
        """
        Find nodes closest to a target ID via iterative lookup.
        
        Args:
            target_id: ID to find nodes near
            
        Returns:
            Closest nodes found, sorted by distance
        """
        # Start with closest known nodes
        closest = self.routing_table.get_closest(target_id, K)
        if not closest:
            return []

        visited = set()
        
        # Iterative lookup
        while True:
            # Filter out already visited nodes and pick ALPHA closest
            to_query = [n for n in closest if n.node_id not in visited][:ALPHA]
            if not to_query:
                break

            # Query nodes in parallel
            tasks = [self.call_rpc(node, "find_node", {"target_id": target_id}) for node in to_query]
            results = await asyncio.gather(*tasks)

            new_nodes_found = False
            for i, response in enumerate(results):
                visited.add(to_query[i].node_id)
                if response and "nodes" in response:
                    for node_dict in response["nodes"]:
                        node = NodeInfo.from_dict(node_dict)
                        if node.node_id != self.node_id and self.routing_table.add_contact(node):
                            new_nodes_found = True
            
            if not new_nodes_found:
                # Re-calculate closest nodes from updated routing table
                current_closest = self.routing_table.get_closest(target_id, K)
                if all(n.node_id in visited for n in current_closest[:ALPHA]):
                    break
                closest = current_closest
            else:
                closest = self.routing_table.get_closest(target_id, K)

        return closest

    async def store(self, key: str, value: Any) -> bool:
        """
        Store a value in the DHT.
        
        Args:
            key: Storage key (e.g., DID)
            value: Value to store
            
        Returns:
            True if stored successfully
        """
        # Store locally
        self.storage.store(key, value)

        # Find closest nodes and replicate
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        closest = await self.lookup_node(key_hash)

        # Send STORE RPCs to closest nodes
        tasks = [self.call_rpc(node, "store", {"key": key, "value": value}) for node in closest]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r and r.get("success"))
        logger.debug(f"Stored {key}: replicated to {success_count}/{len(closest)} nodes")
        return success_count > 0 or not closest

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the DHT via iterative lookup.
        
        Args:
            key: Storage key
            
        Returns:
            Value if found, None otherwise
        """
        # Check local storage first
        value = self.storage.get(key)
        if value is not None:
            return value

        # Find closest nodes and query
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        closest = self.routing_table.get_closest(key_hash, K)
        
        visited = set()
        
        while True:
            to_query = [n for n in closest if n.node_id not in visited][:ALPHA]
            if not to_query:
                break
                
            tasks = [self.call_rpc(node, "find_value", {"key": key}) for node in to_query]
            results = await asyncio.gather(*tasks)
            
            for i, response in enumerate(results):
                visited.add(to_query[i].node_id)
                if not response:
                    continue
                    
                if "value" in response:
                    # Found it! Store locally and return
                    val = response["value"]
                    self.storage.store(key, val)
                    return val
                
                if "nodes" in response:
                    # Didn't find it here, but got closer nodes
                    for node_dict in response["nodes"]:
                        node = NodeInfo.from_dict(node_dict)
                        if node.node_id != self.node_id:
                            self.routing_table.add_contact(node)
            
            # Update closest nodes for next iteration
            closest = self.routing_table.get_closest(key_hash, K)
            if all(n.node_id in visited for n in closest[:ALPHA]):
                break

        logger.debug(f"Lookup {key}: not found after querying {len(visited)} nodes")
        return None

    # RPC Handlers

    async def _handle_ping(self, sender: NodeInfo, data: dict) -> dict:
        """Handle PING RPC."""
        self.routing_table.add_contact(sender)
        return {"node_id": self.node_id}

    async def _handle_find_node(self, sender: NodeInfo, data: dict) -> dict:
        """Handle FIND_NODE RPC."""
        self.routing_table.add_contact(sender)
        target_id = data.get("target_id", "")
        closest = self.routing_table.get_closest(target_id, K)
        return {"nodes": [n.to_dict() for n in closest]}

    async def _handle_find_value(self, sender: NodeInfo, data: dict) -> dict:
        """Handle FIND_VALUE RPC."""
        self.routing_table.add_contact(sender)
        key = data.get("key", "")

        value = self.storage.get(key)
        if value is not None:
            return {"value": value}

        # Return closest nodes if we don't have the value
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        closest = self.routing_table.get_closest(key_hash, K)
        return {"nodes": [n.to_dict() for n in closest]}

    async def _handle_store(self, sender: NodeInfo, data: dict) -> dict:
        """Handle STORE RPC."""
        self.routing_table.add_contact(sender)
        key = data.get("key", "")
        value = data.get("value")

        if key and value is not None:
            self.storage.store(key, value)
            return {"success": True}

        return {"success": False}

    def get_stats(self) -> dict[str, Any]:
        """Get DHT node statistics."""
        return {
            "node_id": self.node_id[:16] + "...",
            "host": self.host,
            "port": self.port,
            "contacts": self.routing_table.contact_count(),
            "stored_values": len(self.storage),
            "running": self._running,
        }


class DHTProtocol(asyncio.DatagramProtocol):
    """UDP protocol for DHT messages."""

    def __init__(self, node: DHTNode):
        self.node = node
        self.transport: Optional[asyncio.DatagramTransport] = None

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Handle incoming datagram."""
        try:
            message = json.loads(data.decode())
            asyncio.create_task(self._handle_message(message, addr))
        except Exception as e:
            logger.error(f"Error processing datagram: {e}")

    async def _handle_message(self, message: dict, addr: tuple[str, int]) -> None:
        """Process incoming RPC message or response."""
        request_id = message.get("request_id")
        if not request_id:
            return

        if "response" in message:
            # Handle RPC response
            future = self.node._pending_requests.get(request_id)
            if future and not future.done():
                future.set_result(message["response"])
            return

        # Handle incoming RPC request
        rpc_type = message.get("type", "")
        sender_id = message.get("sender_id", "")

        sender = NodeInfo(
            node_id=sender_id,
            host=addr[0],
            port=addr[1],
        )

        handler = self.node._rpc_handlers.get(rpc_type)
        if handler:
            response = await handler(sender, message.get("data", {}))
            self._send_response(request_id, response, addr)

    def send_message(self, message: dict, addr: tuple[str, int]) -> None:
        """Send a message to a remote address."""
        if self.transport:
            msg = json.dumps(message).encode()
            self.transport.sendto(msg, addr)

    def _send_response(self, request_id: str, response: dict, addr: tuple[str, int]) -> None:
        """Send RPC response."""
        message = {
            "request_id": request_id,
            "response": response,
        }
        self.send_message(message, addr)


class DIDResolver:
    """
    Resolve DIDs using the DHT.
    
    Provides high-level interface for DID resolution.
    """

    def __init__(self, dht_node: DHTNode):
        """
        Initialize resolver.
        
        Args:
            dht_node: DHT node for lookups
        """
        self.dht = dht_node
        self._cache: dict[str, tuple[dict, float]] = {}  # did -> (doc, timestamp)
        self._cache_ttl = 300  # 5 minutes

    async def resolve(self, did: str) -> Optional[dict]:
        """
        Resolve a DID to its document.
        
        Args:
            did: DID to resolve
            
        Returns:
            DID document dict if found
        """
        # Check cache
        if did in self._cache:
            doc, timestamp = self._cache[did]
            if time.time() - timestamp < self._cache_ttl:
                return doc

        # Lookup in DHT
        doc = await self.dht.get(did)

        if doc:
            self._cache[did] = (doc, time.time())

        return doc

    async def publish(self, did: str, document: dict) -> bool:
        """
        Publish a DID document to the DHT.
        
        Args:
            did: DID being published
            document: DID document
            
        Returns:
            True if published successfully
        """
        success = await self.dht.store(did, document)

        if success:
            self._cache[did] = (document, time.time())

        return success
