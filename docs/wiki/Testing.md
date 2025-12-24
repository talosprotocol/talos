# Testing Guide

## Test Suite Overview

BMP has comprehensive test coverage:

| Test Module | Tests | Coverage |
|-------------|-------|----------|
| `test_crypto.py` | 16 | Cryptographic primitives |
| `test_blockchain.py` | 14 | Basic blockchain ops |
| `test_blockchain_production.py` | 32 | Production features |
| `test_validation.py` | 19 | Block validation engine |
| `test_acl.py` | 16 | Access control lists |
| `test_session.py` | 16 | Double Ratchet protocol |
| `test_sdk.py` | 19 | Python SDK |
| `test_light.py` | 24 | Light client mode |
| `test_did_dht.py` | 41 | DIDs and DHT |
| `test_message.py` | 11 | Message protocol |
| `test_media.py` | 27 | File transfer |
| `test_integration.py` | 7 | End-to-end flows |
| `test_p2p.py` | 15 | P2P networking |
| `test_p2p_coverage.py` | 10 | P2P Coverage (New) |
| `test_cli_coverage.py` | 10 | CLI Coverage (New) |
| `test_sync_coverage.py` | 8 | Sync Coverage (New) |
| `test_engine_coverage.py` | 7 | Engine Coverage (New) |
| **Total** | **462** | **79%** |

## Running Tests

### All Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Parallel execution
pytest tests/ -n auto
```

### Specific Modules

```bash
pytest tests/test_crypto.py -v
pytest tests/test_blockchain.py -v
pytest tests/test_blockchain_production.py -v
pytest tests/test_media.py -v
```

### By Category

```bash
# Only unit tests
pytest tests/ -m "not integration"

# Only integration tests
pytest tests/ -m integration

# Only production tests
pytest tests/test_blockchain_production.py
```

## Test Categories

### Cryptography Tests

```python
class TestKeyPair:
    def test_keypair_generation()
    def test_keypair_serialization()

class TestSignatures:
    def test_sign_and_verify()
    def test_invalid_signature_fails()
    def test_tampered_message_fails()

class TestEncryption:
    def test_encrypt_decrypt_roundtrip()
    def test_shared_secret_derivation()
    def test_different_nonces()
```

### Blockchain Tests

```python
class TestBlock:
    def test_block_creation()
    def test_block_hash_changes_with_content()
    def test_block_mining()

class TestBlockchain:
    def test_blockchain_creation()
    def test_add_and_mine_data()
    def test_chain_validation()
    def test_tampered_chain_fails()

class TestAtomicPersistence:
    def test_save_creates_file()
    def test_save_load_roundtrip()
    def test_save_atomic_no_partial_writes()

class TestChainSync:
    def test_should_accept_chain_more_work()
    def test_replace_valid_longer_chain()
    def test_reject_invalid_chain()
```

### Media Tests

```python
class TestMimeTypeDetection:
    def test_common_extensions()
    def test_unknown_extension()

class TestMediaFile:
    def test_create_from_path()
    def test_file_hash_calculation()
    def test_chunking()

class TestTransferManager:
    def test_create_transfer()
    def test_progress_tracking()
    def test_concurrent_transfers()
```

## Writing New Tests

### Test Structure

```python
import pytest
from src.core.blockchain import Blockchain

class TestNewFeature:
    """Tests for new feature."""
    
    def test_basic_functionality(self):
        """Test the happy path."""
        bc = Blockchain(difficulty=1)
        result = bc.new_method()
        assert result == expected
    
    def test_edge_case(self):
        """Test edge cases."""
        bc = Blockchain(difficulty=1)
        with pytest.raises(ValueError):
            bc.new_method(invalid_input)
    
    @pytest.fixture
    def sample_data(self):
        """Fixture for test data."""
        return {"test": "data"}
    
    def test_with_fixture(self, sample_data):
        """Test using fixture."""
        bc = Blockchain(difficulty=1)
        bc.add_data(sample_data)
        assert len(bc.pending_data) == 1
```

### Async Tests

```python
import pytest

class TestAsyncFeature:
    
    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test async functionality."""
        result = await async_function()
        assert result is not None
```

### Temporary Files

```python
import tempfile
from pathlib import Path

class TestPersistence:
    
    def test_save_load(self):
        """Test with temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.json"
            
            bc = Blockchain(difficulty=1)
            bc.save(path)
            
            loaded = Blockchain.load(path)
            assert len(loaded) == len(bc)
```

## Test Configuration

### pytest.ini / pyproject.toml

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
markers = [
    "integration: marks tests as integration tests",
    "slow: marks tests as slow",
]
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -e ".[dev]"
      
      - name: Run tests
        run: pytest tests/ -v --cov=src
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Benchmarks

```bash
# Run benchmark suite
python -m benchmarks.run_benchmarks

# Output includes:
# - Crypto operations (sign, verify, encrypt)
# - Blockchain operations (mine, validate, lookup)
# - Chunking operations (chunk, reassemble)
```

See [Benchmarks](Benchmarks) for detailed results.
