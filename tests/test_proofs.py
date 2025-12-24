"""
Tests for cryptographic proof verification functions.

These tests cover:
- Block hash verification
- Merkle root verification
- Proof of Work target verification
- Chain link verification
- Signature verification (single and batch)
- Merkle proof verification
- Double hash verification
"""

import hashlib
import json
import pytest
from src.core.validation.proofs import (
    verify_block_hash,
    verify_merkle_root,
    verify_pow_target,
    verify_chain_link,
    verify_signature,
    batch_verify_signatures,
    verify_merkle_proof,
    verify_double_hash,
)
from src.core.crypto import Wallet


class TestVerifyBlockHash:
    """Tests for block hash verification."""
    
    def test_valid_block_hash(self):
        """Verify a correctly hashed block."""
        block = {
            "index": 1,
            "timestamp": 1234567890.0,
            "data": {"messages": []},
            "previous_hash": "0" * 64,
            "nonce": 42,
            "merkle_root": "abc123",
        }
        # Calculate expected hash
        hash_input = json.dumps({
            "index": block["index"],
            "timestamp": block["timestamp"],
            "data": block["data"],
            "previous_hash": block["previous_hash"],
            "nonce": block["nonce"],
            "merkle_root": block["merkle_root"],
        }, sort_keys=True)
        expected = hashlib.sha256(hash_input.encode()).hexdigest()
        block["hash"] = expected
        
        is_valid, calc = verify_block_hash(block)
        assert is_valid is True
        assert calc == expected
    
    def test_invalid_block_hash(self):
        """Detect tampered block hash."""
        block = {
            "index": 1,
            "timestamp": 1234567890.0,
            "data": {"messages": []},
            "previous_hash": "0" * 64,
            "nonce": 42,
            "merkle_root": "",
            "hash": "invalid_hash",
        }
        
        is_valid, _ = verify_block_hash(block)
        assert is_valid is False


class TestVerifyMerkleRoot:
    """Tests for Merkle root verification."""
    
    def test_empty_messages(self):
        """Empty messages should hash to empty hash."""
        empty_hash = hashlib.sha256(b"").hexdigest()
        assert verify_merkle_root([], empty_hash) is True
    
    def test_single_message(self):
        """Single message Merkle root."""
        msg = {"content": "hello"}
        msg_hash = hashlib.sha256(json.dumps(msg, sort_keys=True).encode()).hexdigest()
        assert verify_merkle_root([msg], msg_hash) is True
    
    def test_two_messages(self):
        """Two message Merkle root."""
        msgs = [{"a": 1}, {"b": 2}]
        h1 = hashlib.sha256(json.dumps(msgs[0], sort_keys=True).encode()).hexdigest()
        h2 = hashlib.sha256(json.dumps(msgs[1], sort_keys=True).encode()).hexdigest()
        root = hashlib.sha256((h1 + h2).encode()).hexdigest()
        
        assert verify_merkle_root(msgs, root) is True
    
    def test_invalid_root(self):
        """Invalid Merkle root should fail."""
        msgs = [{"a": 1}]
        assert verify_merkle_root(msgs, "wrong") is False
    
    def test_odd_message_count(self):
        """Odd number of messages (duplication)."""
        msgs = [{"a": 1}, {"b": 2}, {"c": 3}]
        # Calculate expected
        h1 = hashlib.sha256(json.dumps(msgs[0], sort_keys=True).encode()).hexdigest()
        h2 = hashlib.sha256(json.dumps(msgs[1], sort_keys=True).encode()).hexdigest()
        h3 = hashlib.sha256(json.dumps(msgs[2], sort_keys=True).encode()).hexdigest()
        
        # Level 1: h1+h2, h3+h3
        l1_0 = hashlib.sha256((h1 + h2).encode()).hexdigest()
        l1_1 = hashlib.sha256((h3 + h3).encode()).hexdigest()
        
        # Level 2: root
        root = hashlib.sha256((l1_0 + l1_1).encode()).hexdigest()
        
        assert verify_merkle_root(msgs, root) is True


class TestVerifyPowTarget:
    """Tests for PoW target verification."""
    
    def test_meets_target(self):
        """Hash with enough leading zeros."""
        assert verify_pow_target("0000abc123", 4) is True
        assert verify_pow_target("00xyz", 2) is True
        assert verify_pow_target("0a", 1) is True
    
    def test_fails_target(self):
        """Hash without enough leading zeros."""
        assert verify_pow_target("abc", 1) is False
        assert verify_pow_target("0abc", 2) is False
    
    def test_zero_difficulty(self):
        """Zero difficulty always passes."""
        assert verify_pow_target("anything", 0) is True


class TestVerifyChainLink:
    """Tests for chain link verification."""
    
    def test_genesis_block(self):
        """Genesis block with all-zero previous hash."""
        genesis = {"previous_hash": "0" * 64}
        assert verify_chain_link(genesis, None) is True
    
    def test_valid_chain_link(self):
        """Valid chain link."""
        prev = {"hash": "abc123"}
        current = {"previous_hash": "abc123"}
        assert verify_chain_link(current, prev) is True
    
    def test_invalid_chain_link(self):
        """Broken chain link."""
        prev = {"hash": "abc123"}
        current = {"previous_hash": "xyz789"}
        assert verify_chain_link(current, prev) is False
    
    def test_invalid_genesis(self):
        """Genesis with wrong previous hash."""
        genesis = {"previous_hash": "abc"}
        assert verify_chain_link(genesis, None) is False


class TestVerifySignature:
    """Tests for signature verification."""
    
    def test_valid_signature(self):
        """Valid Ed25519 signature."""
        wallet = Wallet.generate("test")
        msg = b"Hello, World!"
        sig = wallet.sign(msg)
        
        assert verify_signature(msg, sig, wallet.signing_keys.public_key) is True
    
    def test_invalid_signature(self):
        """Modified signature."""
        wallet = Wallet.generate("test")
        msg = b"Hello!"
        sig = wallet.sign(msg)
        
        # Tamper with signature
        bad_sig = bytes([sig[0] ^ 0xFF]) + sig[1:]
        assert verify_signature(msg, bad_sig, wallet.signing_keys.public_key) is False
    
    def test_wrong_message(self):
        """Signature for different message."""
        wallet = Wallet.generate("test")
        msg1 = b"Hello!"
        msg2 = b"Goodbye!"
        sig = wallet.sign(msg1)
        
        assert verify_signature(msg2, sig, wallet.signing_keys.public_key) is False
    
    def test_wrong_key(self):
        """Signature with different key."""
        wallet1 = Wallet.generate("test1")
        wallet2 = Wallet.generate("test2")
        msg = b"Hello!"
        sig = wallet1.sign(msg)
        
        assert verify_signature(msg, sig, wallet2.signing_keys.public_key) is False


class TestBatchVerifySignatures:
    """Tests for batch signature verification."""
    
    def test_empty_batch(self):
        """Empty input returns empty list."""
        assert batch_verify_signatures([], [], []) == []
    
    def test_single_signature(self):
        """Single signature batch."""
        wallet = Wallet.generate("test")
        msg = b"Test"
        sig = wallet.sign(msg)
        
        results = batch_verify_signatures([msg], [sig], [wallet.signing_keys.public_key])
        assert results == [True]
    
    def test_multiple_signatures(self):
        """Multiple signature batch."""
        wallets = [Wallet.generate(f"test{i}") for i in range(3)]
        msgs = [b"Msg1", b"Msg2", b"Msg3"]
        sigs = [w.sign(m) for m, w in zip(msgs, wallets)]
        pubkeys = [w.signing_keys.public_key for w in wallets]
        
        results = batch_verify_signatures(msgs, sigs, pubkeys)
        assert results == [True, True, True]
    
    def test_mixed_valid_invalid(self):
        """Batch with some invalid signatures."""
        wallet = Wallet.generate("test")
        msgs = [b"Msg1", b"Msg2"]
        sig1 = wallet.sign(msgs[0])
        sig2 = b"x" * 64  # Invalid
        
        results = batch_verify_signatures(
            msgs, [sig1, sig2], [wallet.signing_keys.public_key, wallet.signing_keys.public_key]
        )
        assert results == [True, False]
    
    def test_sequential_verification(self):
        """Non-parallel verification."""
        wallet = Wallet.generate("test")
        msg = b"Test"
        sig = wallet.sign(msg)
        
        results = batch_verify_signatures(
            [msg], [sig], [wallet.signing_keys.public_key], parallel=False
        )
        assert results == [True]
    
    def test_mismatched_lengths(self):
        """Mismatched input lengths raise error."""
        with pytest.raises(ValueError):
            batch_verify_signatures([b"a"], [b"b", b"c"], [b"d"])


class TestVerifyMerkleProof:
    """Tests for Merkle proof verification."""
    
    def test_empty_proof(self):
        """Empty proof - data is root."""
        data_hash = "abc123"
        assert verify_merkle_proof(data_hash, [], data_hash) is True
    
    def test_single_step_left(self):
        """Single step proof with left sibling."""
        data = "data123"
        sibling = "sibling456"
        root = hashlib.sha256((sibling + data).encode()).hexdigest()
        
        proof = [(sibling, "left")]
        assert verify_merkle_proof(data, proof, root) is True
    
    def test_single_step_right(self):
        """Single step proof with right sibling."""
        data = "data123"
        sibling = "sibling456"
        root = hashlib.sha256((data + sibling).encode()).hexdigest()
        
        proof = [(sibling, "right")]
        assert verify_merkle_proof(data, proof, root) is True
    
    def test_invalid_proof(self):
        """Invalid proof path."""
        assert verify_merkle_proof("data", [("bad", "left")], "root") is False


class TestVerifyDoubleHash:
    """Tests for double SHA-256 verification."""
    
    def test_valid_double_hash(self):
        """Correct double hash."""
        data = b"test data"
        first = hashlib.sha256(data).digest()
        expected = hashlib.sha256(first).hexdigest()
        
        assert verify_double_hash(data, expected) is True
    
    def test_invalid_double_hash(self):
        """Wrong expected hash."""
        assert verify_double_hash(b"data", "wrong") is False
