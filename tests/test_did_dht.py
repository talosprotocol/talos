"""
Tests for Decentralized Identifiers (DIDs) and DHT.

Tests cover:
- DID document creation
- Verification methods
- Service endpoints
- DID manager
- DHT routing table
- DHT storage
- DID resolution
"""

import pytest
import tempfile
import hashlib
from pathlib import Path
from dataclasses import dataclass

from src.core.did import (
    DIDDocument,
    DIDManager,
    VerificationMethod,
    ServiceEndpoint,
    validate_did,
    DID_METHOD,
)
from src.network.dht import (
    NodeInfo,
    DHTNode,
    DHTStorage,
    RoutingTable,
    DIDResolver,
    xor_distance,
    bucket_index,
    generate_node_id,
)


# Mock keypair for testing
@dataclass
class MockKeypair:
    public_key: bytes
    private_key: bytes = b""


class TestVerificationMethod:
    """Tests for VerificationMethod."""
    
    def test_create_verification_method(self):
        """Test creating a verification method."""
        method = VerificationMethod(
            id="did:talos:abc123#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:talos:abc123",
            public_key_multibase="z123abc",
        )
        
        assert method.id == "did:talos:abc123#key-1"
        assert method.type == "Ed25519VerificationKey2020"
    
    def test_serialization(self):
        """Test to_dict/from_dict."""
        method = VerificationMethod(
            id="did:talos:test#key-1",
            type="Ed25519VerificationKey2020",
            controller="did:talos:test",
            public_key_multibase="zABC123",
        )
        
        data = method.to_dict()
        loaded = VerificationMethod.from_dict(data)
        
        assert loaded.id == method.id
        assert loaded.public_key_multibase == method.public_key_multibase


class TestServiceEndpoint:
    """Tests for ServiceEndpoint."""
    
    def test_create_service(self):
        """Test creating a service endpoint."""
        service = ServiceEndpoint(
            id="did:talos:abc#messaging",
            type="TalosMessaging",
            service_endpoint="wss://example.com:8765",
            description="Messaging service",
        )
        
        assert service.type == "TalosMessaging"
        assert "example.com" in service.service_endpoint
    
    def test_serialization(self):
        """Test to_dict/from_dict."""
        service = ServiceEndpoint(
            id="did:talos:abc#svc",
            type="TestService",
            service_endpoint="https://test.com",
        )
        
        data = service.to_dict()
        loaded = ServiceEndpoint.from_dict(data)
        
        assert loaded.id == service.id
        assert loaded.service_endpoint == service.service_endpoint


class TestDIDDocument:
    """Tests for DIDDocument."""
    
    def test_create_document(self):
        """Test creating a DID document."""
        doc = DIDDocument(id="did:talos:abc123")
        
        assert doc.id == "did:talos:abc123"
        assert len(doc.verification_method) == 0
    
    def test_add_verification_method(self):
        """Test adding verification methods."""
        doc = DIDDocument(id="did:talos:test")
        
        doc.add_verification_method(
            key_id="#key-1",
            key_type="Ed25519VerificationKey2020",
            public_key=b"publickey123",
            purposes=["authentication", "assertionMethod"],
        )
        
        assert len(doc.verification_method) == 1
        assert len(doc.authentication) == 1
        assert len(doc.assertion_method) == 1
    
    def test_add_service(self):
        """Test adding service endpoints."""
        doc = DIDDocument(id="did:talos:test")
        
        doc.add_service(
            service_id="#messaging",
            service_type="TalosMessaging",
            endpoint="wss://localhost:8765",
        )
        
        assert len(doc.service) == 1
        assert doc.service[0].type == "TalosMessaging"
    
    def test_get_verification_method(self):
        """Test retrieving verification method."""
        doc = DIDDocument(id="did:talos:test")
        doc.add_verification_method(
            key_id="#key-1",
            key_type="Ed25519VerificationKey2020",
            public_key=b"pubkey",
            purposes=["authentication"],
        )
        
        method = doc.get_verification_method("#key-1")
        assert method is not None
        assert method.type == "Ed25519VerificationKey2020"
    
    def test_get_service(self):
        """Test retrieving service."""
        doc = DIDDocument(id="did:talos:test")
        doc.add_service("#svc", "TestType", "https://test.com")
        
        svc = doc.get_service("#svc")
        assert svc is not None
        assert svc.type == "TestType"
    
    def test_to_json(self):
        """Test JSON serialization."""
        doc = DIDDocument(id="did:talos:test123")
        doc.add_verification_method(
            "#key-1", "Ed25519VerificationKey2020",
            b"pubkey", ["authentication"]
        )
        
        json_str = doc.to_json()
        
        assert "did:talos:test123" in json_str
        assert "@context" in json_str
    
    def test_from_json(self):
        """Test JSON deserialization."""
        doc = DIDDocument(id="did:talos:roundtrip")
        doc.add_verification_method(
            "#key-1", "Ed25519VerificationKey2020",
            b"pubkey", ["authentication"]
        )
        doc.add_service("#svc", "TestService", "https://test.com")
        
        json_str = doc.to_json()
        loaded = DIDDocument.from_json(json_str)
        
        assert loaded.id == doc.id
        assert len(loaded.verification_method) == 1
        assert len(loaded.service) == 1


class TestDIDManager:
    """Tests for DIDManager."""
    
    @pytest.fixture
    def keypair(self):
        return MockKeypair(public_key=b"x" * 32)
    
    def test_create_did(self, keypair):
        """Test DID creation."""
        manager = DIDManager(keypair)
        did = manager.create_did()
        
        assert did.startswith("did:talos:")
        assert len(did.split(":")) == 3
    
    def test_create_document(self, keypair):
        """Test document creation."""
        manager = DIDManager(keypair)
        doc = manager.create_document(service_endpoint="wss://test.com:8765")
        
        assert doc.id == manager.did
        assert len(doc.verification_method) == 1
        assert len(doc.service) == 1
    
    def test_document_with_encryption_key(self, keypair):
        """Test document with encryption keypair."""
        enc_keypair = MockKeypair(public_key=b"y" * 32)
        manager = DIDManager(keypair, encryption_keypair=enc_keypair)
        doc = manager.create_document()
        
        # Should have both signing and encryption keys
        assert len(doc.verification_method) == 2
        assert len(doc.key_agreement) == 1
    
    def test_update_service_endpoint(self, keypair):
        """Test updating service endpoint."""
        manager = DIDManager(keypair)
        manager.create_document(service_endpoint="wss://old.com")
        
        manager.update_service_endpoint("wss://new.com")
        
        svc = manager.document.get_service("#messaging")
        assert svc is not None
        assert "new.com" in svc.service_endpoint
    
    def test_persistence(self, keypair):
        """Test save/load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "did.json"
            
            manager1 = DIDManager(keypair, storage_path=path)
            manager1.create_document(service_endpoint="wss://test.com")
            manager1.save()
            
            # Load into new manager
            manager2 = DIDManager(keypair, storage_path=path)
            manager2.load()
            
            assert manager2.document.id == manager1.document.id


class TestValidateDID:
    """Tests for DID validation."""
    
    def test_valid_did(self):
        """Test valid DID format."""
        valid_did = "did:talos:" + "a" * 32
        assert validate_did(valid_did) is True
    
    def test_invalid_method(self):
        """Test invalid method."""
        assert validate_did("did:other:" + "a" * 32) is False
    
    def test_invalid_format(self):
        """Test invalid format."""
        assert validate_did("not-a-did") is False
        assert validate_did("did:talos:") is False
        assert validate_did("did:talos:short") is False


class TestDHTHelpers:
    """Tests for DHT helper functions."""
    
    def test_xor_distance(self):
        """Test XOR distance calculation."""
        id1 = "0" * 64
        id2 = "f" * 64
        
        distance = xor_distance(id1, id2)
        assert distance > 0
        
        # Same ID = 0 distance
        assert xor_distance(id1, id1) == 0
    
    def test_bucket_index(self):
        """Test bucket index calculation."""
        local_id = "0" * 64
        
        # Same ID = bucket 0
        assert bucket_index(local_id, local_id) == 0
        
        # Different ID = higher bucket
        far_id = "8" + "0" * 63
        assert bucket_index(local_id, far_id) > 0
    
    def test_generate_node_id(self):
        """Test node ID generation."""
        id1 = generate_node_id()
        id2 = generate_node_id()
        
        assert len(id1) == 64
        assert id1 != id2  # Random
        
        # With seed data
        id3 = generate_node_id(b"seed")
        id4 = generate_node_id(b"seed")
        assert id3 == id4  # Deterministic


class TestNodeInfo:
    """Tests for NodeInfo."""
    
    def test_create_node_info(self):
        """Test creating node info."""
        node = NodeInfo(
            node_id="abc123",
            host="192.168.1.1",
            port=8765,
        )
        
        assert node.address == ("192.168.1.1", 8765)
    
    def test_serialization(self):
        """Test to_dict/from_dict."""
        node = NodeInfo("id123", "localhost", 8080)
        
        data = node.to_dict()
        loaded = NodeInfo.from_dict(data)
        
        assert loaded.node_id == node.node_id
        assert loaded.address == node.address


class TestRoutingTable:
    """Tests for RoutingTable."""
    
    def test_create_table(self):
        """Test creating routing table."""
        table = RoutingTable(generate_node_id())
        assert table.contact_count() == 0
    
    def test_add_contact(self):
        """Test adding contacts."""
        local_id = generate_node_id()
        table = RoutingTable(local_id)
        
        node = NodeInfo(generate_node_id(), "localhost", 8000)
        result = table.add_contact(node)
        
        assert result is True
        assert table.contact_count() == 1
    
    def test_add_self_rejected(self):
        """Test that adding self is rejected."""
        local_id = generate_node_id()
        table = RoutingTable(local_id)
        
        self_node = NodeInfo(local_id, "localhost", 8000)
        result = table.add_contact(self_node)
        
        assert result is False
    
    def test_get_closest(self):
        """Test getting closest contacts."""
        local_id = generate_node_id()
        table = RoutingTable(local_id)
        
        # Add some nodes
        for _ in range(5):
            node = NodeInfo(generate_node_id(), "localhost", 8000)
            table.add_contact(node)
        
        target = generate_node_id()
        closest = table.get_closest(target, 3)
        
        assert len(closest) <= 3
    
    def test_remove_contact(self):
        """Test removing contacts."""
        local_id = generate_node_id()
        table = RoutingTable(local_id)
        
        node = NodeInfo(generate_node_id(), "localhost", 8000)
        table.add_contact(node)
        
        result = table.remove_contact(node.node_id)
        
        assert result is True
        assert table.contact_count() == 0


class TestDHTStorage:
    """Tests for DHTStorage."""
    
    def test_store_and_get(self):
        """Test storing and retrieving values."""
        storage = DHTStorage()
        
        storage.store("key1", {"value": "test"})
        result = storage.get("key1")
        
        assert result == {"value": "test"}
    
    def test_get_missing(self):
        """Test getting missing key."""
        storage = DHTStorage()
        assert storage.get("missing") is None
    
    def test_delete(self):
        """Test deleting values."""
        storage = DHTStorage()
        storage.store("key", "value")
        
        result = storage.delete("key")
        
        assert result is True
        assert storage.get("key") is None
    
    def test_expiry(self):
        """Test value expiry."""
        storage = DHTStorage(max_age=0)  # Immediate expiry
        
        storage.store("key", "value")
        
        import time
        time.sleep(0.01)
        
        assert storage.get("key") is None


class TestDHTNode:
    """Tests for DHTNode."""
    
    def test_create_node(self):
        """Test creating DHT node."""
        node = DHTNode(host="127.0.0.1", port=8468)
        
        assert node.node_id is not None
        assert len(node.node_id) == 64
    
    def test_node_with_id(self):
        """Test creating node with specific ID."""
        custom_id = "a" * 64
        node = DHTNode(node_id=custom_id)
        
        assert node.node_id == custom_id
    
    def test_node_info(self):
        """Test getting node info."""
        node = DHTNode(host="192.168.1.1", port=9000)
        info = node.node_info
        
        assert info.host == "192.168.1.1"
        assert info.port == 9000
    
    @pytest.mark.asyncio
    async def test_store_and_get(self):
        """Test storing and retrieving via node."""
        node = DHTNode()
        
        await node.store("test_key", {"data": "test"})
        result = await node.get("test_key")
        
        assert result == {"data": "test"}
    
    @pytest.mark.asyncio
    async def test_bootstrap(self):
        """Test bootstrapping."""
        node = DHTNode()
        
        bootstrap_nodes = [
            NodeInfo(generate_node_id(), "192.168.1.1", 8000),
            NodeInfo(generate_node_id(), "192.168.1.2", 8000),
        ]
        
        added = await node.bootstrap(bootstrap_nodes)
        assert added == 2
    
    def test_get_stats(self):
        """Test getting statistics."""
        node = DHTNode()
        stats = node.get_stats()
        
        assert "node_id" in stats
        assert "contacts" in stats
        assert "stored_values" in stats


class TestDIDResolver:
    """Tests for DIDResolver."""
    
    @pytest.mark.asyncio
    async def test_publish_and_resolve(self):
        """Test publishing and resolving DID."""
        node = DHTNode()
        resolver = DIDResolver(node)
        
        did = "did:talos:" + "a" * 32
        doc = {"id": did, "verificationMethod": []}
        
        await resolver.publish(did, doc)
        result = await resolver.resolve(did)
        
        assert result is not None
        assert result["id"] == did
    
    @pytest.mark.asyncio
    async def test_resolve_not_found(self):
        """Test resolving non-existent DID."""
        node = DHTNode()
        resolver = DIDResolver(node)
        
        result = await resolver.resolve("did:talos:nonexistent")
        assert result is None
