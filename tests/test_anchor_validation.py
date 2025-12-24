
import pytest
import base64
from src.core.blockchain import Block
from src.core.validation.engine import ValidationEngine, ValidationErrorCode
from src.core.crypto import Wallet

@pytest.fixture
def oracle():
    return Wallet.generate("Oracle")

@pytest.fixture
def block():
    block = Block(
        index=1,
        timestamp=1234567890.0,
        data={},
        previous_hash="0" * 64,
        nonce=0
    )
    # Force hash calculation
    _ = block.hash
    return block

@pytest.mark.asyncio
async def test_cross_chain_no_anchors(block):
    engine = ValidationEngine(enable_cross_chain=True)
    # Should pass (optional by default)
    result = await engine._validate_cross_chain(block)
    assert len(result) == 0

@pytest.mark.asyncio
async def test_cross_chain_valid_anchor(block, oracle):
    # Oracle signs the block hash
    sig = oracle.sign(block.hash.encode())
    sig_b64 = base64.b64encode(sig).decode()
    
    block.data = {
        "anchors": [
            {
                "oracle": oracle.address,
                "signature": sig_b64,
                "statement": block.hash
            }
        ]
    }
    
    engine = ValidationEngine(
        enable_cross_chain=True,
        trusted_anchors={oracle.address}
    )
    
    errors = await engine._validate_cross_chain(block)
    assert len(errors) == 0

@pytest.mark.asyncio
async def test_cross_chain_untrusted_oracle(block, oracle):
    sig = oracle.sign(block.hash.encode())
    sig_b64 = base64.b64encode(sig).decode()
    
    block.data = {
        "anchors": [
            {
                "oracle": oracle.address,
                "signature": sig_b64,
                "statement": block.hash
            }
        ]
    }
    
    # Engine trusts NO ONE
    engine = ValidationEngine(
        enable_cross_chain=True,
        trusted_anchors=set() 
    )
    
    errors = await engine._validate_cross_chain(block)
    assert len(errors) == 1
    assert errors[0].code == ValidationErrorCode.EXTERNAL_VERIFICATION_FAILED

@pytest.mark.asyncio
async def test_cross_chain_invalid_signature(block, oracle):
    # Sign something else
    sig = oracle.sign(b"malicious_statement")
    sig_b64 = base64.b64encode(sig).decode()
    
    block.data = {
        "anchors": [
            {
                "oracle": oracle.address,
                "signature": sig_b64,
                "statement": block.hash
            }
        ]
    }
    
    engine = ValidationEngine(
        enable_cross_chain=True,
        trusted_anchors={oracle.address}
    )
    
    errors = await engine._validate_cross_chain(block)
    assert len(errors) >= 1
    # Either signature invalid or mismatch depending on how we constructed it
    # Here statement matches, but signature is for different data -> SIGNATURE_INVALID
    assert errors[0].code == ValidationErrorCode.SIGNATURE_INVALID

@pytest.mark.asyncio
async def test_cross_chain_mismatched_statement(block, oracle):
    sig = oracle.sign(b"some_other_hash")
    sig_b64 = base64.b64encode(sig).decode()
    
    block.data = {
        "anchors": [
            {
                "oracle": oracle.address,
                "signature": sig_b64,
                "statement": "some_other_hash"
            }
        ]
    }
    
    engine = ValidationEngine(
        enable_cross_chain=True,
        trusted_anchors={oracle.address}
    )
    
    errors = await engine._validate_cross_chain(block)
    assert len(errors) == 1
    assert errors[0].code == ValidationErrorCode.ANCHOR_MISMATCH
