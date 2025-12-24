"""
Tests for the Talos SDK.

Tests cover:
- Configuration
- Identity management
- TalosClient
- SecureChannel
"""

import pytest
import tempfile
from pathlib import Path

from talos import (
    TalosClient,
    SecureChannel,
    Identity,
    TalosConfig,
)
from talos.channel import ChannelPool
from talos.exceptions import SessionError


class TestTalosConfig:
    """Tests for SDK configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TalosConfig()
        
        assert config.name == "talos-agent"
        assert config.difficulty == 2
        assert config.forward_secrecy is True
    
    def test_config_override(self):
        """Test configuration override."""
        config = TalosConfig(
            name="my-agent",
            difficulty=4,  
            log_level="DEBUG",
        )
        
        assert config.name == "my-agent"
        assert config.difficulty == 4
        assert config.log_level == "DEBUG"
    
    def test_development_config(self):
        """Test development preset."""
        config = TalosConfig.development()
        
        assert config.difficulty == 1
        assert config.log_level == "DEBUG"
    
    def test_production_config(self):
        """Test production preset."""
        config = TalosConfig.production()
        
        assert config.difficulty == 4
        assert config.log_level == "WARNING"
    
    def test_config_persistence(self):
        """Test config save/load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = TalosConfig(
                name="test-agent",
                data_dir=Path(tmpdir),
                difficulty=3,
            )
            
            config_path = Path(tmpdir) / "config.json"
            config.save(config_path)
            
            loaded = TalosConfig.load(config_path)
            
            assert loaded.name == "test-agent"
            assert loaded.difficulty == 3


class TestIdentity:
    """Tests for identity management."""
    
    def test_create_identity(self):
        """Test creating a new identity."""
        identity = Identity.create("test-agent")
        
        assert identity.name == "test-agent"
        assert len(identity.address) == 64  # Hex-encoded 32 bytes
        assert identity.signing_keys is not None
        assert identity.encryption_keys is not None
    
    def test_identity_signing(self):
        """Test signing with identity."""
        identity = Identity.create("signer")
        
        data = b"Hello, World!"
        signature = identity.sign(data)
        
        assert len(signature) == 64  # Ed25519 signature
    
    def test_identity_persistence(self):
        """Test identity save/load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "keys.json"
            
            # Create and save
            identity1 = Identity.create("test")
            identity1.save(path)
            
            # Load
            identity2 = Identity.load(path)
            
            assert identity2.name == "test"
            assert identity2.address == identity1.address
    
    def test_load_or_create(self):
        """Test load_or_create behavior."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "keys.json"
            
            # First call creates
            identity1 = Identity.load_or_create(path, "agent1")
            assert identity1.name == "agent1"
            
            # Second call loads
            identity2 = Identity.load_or_create(path, "agent2")
            assert identity2.name == "agent1"  # Loaded, not created
            assert identity2.address == identity1.address
    
    def test_prekey_bundle(self):
        """Test prekey bundle generation."""
        identity = Identity.create("prekey-test")
        
        bundle = identity.get_prekey_bundle()
        
        assert bundle.identity_key == identity.signing_keys.public_key
        assert bundle.verify()


class TestTalosClient:
    """Tests for the main client."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_create_client(self, temp_dir):
        """Test client creation."""
        config = TalosConfig(name="test", data_dir=temp_dir)
        client = TalosClient.create("test-agent", config)
        
        assert client.identity.name == "test-agent"
        assert not client.is_running
    
    @pytest.mark.asyncio
    async def test_client_start_stop(self, temp_dir):
        """Test client lifecycle."""
        config = TalosConfig(name="test", data_dir=temp_dir)
        client = TalosClient.create("test", config)
        
        # Start
        await client.start()
        assert client.is_running
        
        # Stop
        await client.stop()
        assert not client.is_running
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self, temp_dir):
        """Test async context manager."""
        config = TalosConfig(name="test", data_dir=temp_dir)
        client = TalosClient.create("test", config)
        
        async with client:
            assert client.is_running
        
        assert not client.is_running
    
    def test_get_prekey_bundle(self, temp_dir):
        """Test getting prekey bundle."""
        config = TalosConfig(name="test", data_dir=temp_dir)
        client = TalosClient.create("test", config)
        
        bundle = client.get_prekey_bundle()
        
        assert "identity_key" in bundle
        assert "signed_prekey" in bundle
        assert "prekey_signature" in bundle
    
    @pytest.mark.asyncio
    async def test_session_establishment(self, temp_dir):
        """Test establishing a session between two clients."""
        config1 = TalosConfig(name="alice", data_dir=temp_dir / "alice")
        config2 = TalosConfig(name="bob", data_dir=temp_dir / "bob")
        
        alice = TalosClient.create("alice", config1)
        bob = TalosClient.create("bob", config2)
        
        await alice.start()
        await bob.start()
        
        try:
            # Get Bob's prekey bundle
            bob_bundle = bob.get_prekey_bundle()
            
            # Alice establishes session with Bob
            session = await alice.establish_session(bob.address, bob_bundle)
            
            assert session is not None
            assert alice.has_session(bob.address)
        finally:
            await alice.stop()
            await bob.stop()
    
    def test_stats(self, temp_dir):
        """Test getting stats."""
        config = TalosConfig(name="test", data_dir=temp_dir)
        client = TalosClient.create("test", config)
        
        stats = client.get_stats()
        
        assert "address" in stats
        assert "running" in stats


class TestSecureChannel:
    """Tests for SecureChannel."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.mark.asyncio
    async def test_channel_requires_session(self, temp_dir):
        """Test that channel requires session or bundle."""
        config = TalosConfig(name="test", data_dir=temp_dir)
        client = TalosClient.create("test", config)
        await client.start()
        
        try:
            channel = SecureChannel(client, "fake_peer_id")
            
            with pytest.raises(SessionError):
                await channel.connect()
        finally:
            await client.stop()


class TestChannelPool:
    """Tests for ChannelPool."""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.mark.asyncio
    async def test_pool_creation(self, temp_dir):
        """Test pool creation."""
        config = TalosConfig(name="test", data_dir=temp_dir)
        client = TalosClient.create("test", config)
        
        pool = ChannelPool(client)
        
        assert len(pool) == 0
    
    @pytest.mark.asyncio
    async def test_pool_close_all(self, temp_dir):
        """Test closing all channels."""
        config = TalosConfig(name="test", data_dir=temp_dir)
        client = TalosClient.create("test", config)
        
        pool = ChannelPool(client)
        await pool.close_all()
        
        assert len(pool) == 0
