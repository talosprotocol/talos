# Talos Protocol

> **Secure, Decentralized Communication for the AI Agent Era**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-595%20passing-green.svg)](#testing)
[![Coverage](https://img.shields.io/badge/coverage-82%25-green.svg)](#testing)

## v3.0 Features

| Feature | Status | Description |
|---------|--------|-------------|
| 🔐 **Capability Authorization** | ✅ NEW | Cryptographic tokens, <1ms session-cached auth |
| 🔄 **Double Ratchet** | ✅ | Signal protocol for per-message forward secrecy |
| ✅ **Validation Engine** | ✅ | 5-layer block validation with audit reports |
| 📦 **Python SDK** | ✅ | Clean `TalosClient` and `SecureChannel` API |
| 💡 **Light Client** | ✅ | SPV proof verification, ~99% storage reduction |
| 🆔 **DIDs/DHT** | ✅ | W3C DIDs with Kademlia peer discovery |
| 🤖 **MCP Integration** | ✅ | Secure tool invocation with mandatory auth |
| ⚡ **Performance** | ✅ | 695k auth/sec, <5ms p99 overhead |

```python
# Quick Example
from talos import TalosClient

async with TalosClient.create("my-agent") as client:
    await client.establish_session(peer_id, peer_bundle)
    await client.send(peer_id, b"Hello with forward secrecy!")
```

📖 **[Documentation Wiki](https://github.com/nileshchakraborty/talos/wiki)** | 📚 **[Examples](examples/)** | 📋 **[CHANGELOG](CHANGELOG.md)** | 🗺️ **[Roadmap](docs/ROADMAP_v2.md)**

---

## Why Talos Exists

AI agents are proliferating—but they lack a trustable communication substrate:

| Problem | Current State | Talos Solution |
|---------|---------------|----------------|
| **Identity** | No cryptographic agent identity | Self-sovereign DIDs with keypairs |
| **Authorization** | Centralized OAuth/RBAC | Scoped, expiring capability tokens |
| **Confidentiality** | TLS at best | Per-message forward secrecy (Double Ratchet) |
| **Accountability** | Server logs (trust the operator) | Blockchain-anchored Merkle proofs |
| **Decentralization** | IdPs, brokers, central servers | P2P with DHT discovery |

**Existing tools fail for agents:**
- **HTTP + OAuth** = Centralized trust, no forward secrecy
- **Kafka / SQS** = Infrastructure-heavy, not cryptographic
- **Matrix / Signal** = Human-centric, not agent-native
- **gRPC + mTLS** = No audit trail, no capability model

> **Talos is the missing communication and trust layer for autonomous AI systems—where agents must identify themselves, exchange sensitive data, prove actions, and operate without centralized intermediaries.**

📖 **[Full rationale →](docs/wiki/Why-Talos-Wins.md)** | **[Threat Model →](docs/wiki/Threat-Model.md)** | **[Alternatives →](docs/wiki/Alternatives-Comparison.md)**

---

<truncated>

## MCP Integration

Securely tunnel [Model Context Protocol (MCP)](https://modelcontextprotocol.io) traffic over the blockchain.

### 1. Connect (Client/Agent)

You can use the native CLI command to connect your Agent to a remote tool:

```bash
talos mcp-connect <REMOTE_PEER_ID> --port 8766
```

Or for development, use the example script:

```bash
python examples/mcp_connect_demo.py --peer <REMOTE_PEER_ID>
```

### 2. Serve (Host/Tool)

Expose a local tool (e.g. a filesystem) to a specific remote Agent:

```bash
talos mcp-serve \
  --authorized-peer <AGENT_PEER_ID> \
  --command "npx -y @modelcontextprotocol/server-filesystem /path/to/share"
```

Or for development:

```bash
python examples/mcp_serve_demo.py \
  --authorized-peer <AGENT_PEER_ID> \
  --command "npx -y @modelcontextprotocol/server-filesystem /path/to/share"
```

👉 **[See full MCP Documentation](docs/wiki/MCP-Integration.md)** for architecture and security details.

---

## Evaluation

### Test Suite

```bash
# Run all tests (595 tests)
pytest tests/ -v

# Run specific test modules
pytest tests/test_crypto.py -v               # Cryptographic primitives
pytest tests/test_blockchain.py -v           # Basic blockchain operations
pytest tests/test_validation.py -v           # Block validation engine (19 tests)
pytest tests/test_session.py -v              # Double Ratchet (16 tests)
pytest tests/test_acl.py -v                  # ACL system (16 tests)
pytest tests/test_light.py -v                # Light client (24 tests)
pytest tests/test_did_dht.py -v              # DIDs/DHT (41 tests)
pytest tests/test_sdk.py -v                  # SDK (19 tests)
```

### Security Considerations

| Threat | Mitigation |
|--------|------------|
| Man-in-the-Middle | End-to-end encryption with authenticated key exchange |
| Replay Attacks | Message IDs + timestamps + blockchain ordering |
| Impersonation | Ed25519 digital signatures |
| Message Tampering | Poly1305 MAC + blockchain immutability |
| Metadata Analysis | Future: onion routing integration |

### Performance Metrics (Apple M1/M2)

| Component | Operation | Throughput | Latency |
|-----------|-----------|------------|---------|
| **Crypto** | Ed25519 Verify | ~6,600 ops/s | 0.15ms |
| **Crypto** | ChaCha20 Encrypt | ~295,000 ops/s | 0.003ms |
| **Storage** | LMDB Read | ~3,600,000 ops/s | 0.0003ms |
| **Storage** | LMDB Write | ~2,100,000 ops/s | 0.0005ms |
| **Network** | JSON Serialize | ~1,200,000 ops/s | 0.0008ms |
| **Validation** | Block Validation | ~3,700 blocks/s | 0.27ms |

> **Note**: Results may vary based on hardware and load.

```bash
# Run benchmarks
python -m benchmarks.run_benchmarks
```

---

## Documentation

📚 **Full documentation available in the [Wiki](docs/wiki/)**:

| Guide | Description |
|-------|-------------|
| [🏠 Home](docs/wiki/Home.md) | Overview and quick links |
| [🚀 Getting Started](docs/wiki/Getting-Started.md) | Installation and first steps |
| [🏗️ Architecture](docs/wiki/Architecture.md) | System design and data flows |
| [🔐 Cryptography](docs/wiki/Cryptography.md) | Security model and primitives |
| [⛓️ Blockchain](docs/wiki/Blockchain.md) | Chain design and sync protocol |
| [📁 File Transfer](docs/wiki/File-Transfer.md) | Media exchange protocol |
| [📊 Benchmarks](docs/wiki/Benchmarks.md) | Performance metrics |
| [📖 API Reference](docs/wiki/API-Reference.md) | Complete API documentation |
| [🧪 Testing](docs/wiki/Testing.md) | Test suite and coverage |

---

## Future Work

1. **Post-Quantum Cryptography**: CRYSTALS-Kyber/Dilithium integration
2. **Onion Routing**: Tor-style routing for metadata protection
3. **WebRTC Integration**: Real-time audio/video
4. **TypeScript SDK**: Browser and Node.js support
5. **Formal Verification**: ProVerif/Tamarin security proofs
6. **BFT Consensus**: Byzantine fault-tolerant consensus layer

🔮 **[See Full Future Roadmap](docs/wiki/Future-Improvements.md)**

---

## Directory Structure

```
talos/
├── src/
│   ├── core/           # Blockchain, crypto, validation, session, light, did
│   ├── network/        # P2P networking, DHT
│   ├── mcp_bridge/     # ACL system, MCP integration
│   ├── server/         # Registry server
│   ├── client/         # CLI client
│   └── engine/         # Transmission engine, chunking
├── talos/              # Python SDK
├── examples/           # 8 copy-paste ready examples
├── tests/              # 496 tests
├── deploy/
│   └── helm/talos/     # Kubernetes Helm chart
├── Dockerfile          # Multi-stage production image
├── docker-compose.yml  # Local development
└── docs/wiki/          # 22 documentation pages
```

---

## References

[1] A. Acquisti and R. Gross, "Imagined Communities: Awareness, Information Sharing, and Privacy on the Facebook," *Privacy Enhancing Technologies*, 2006.

[2] R. Dingledine, N. Mathewson, and P. Syverson, "Tor: The Second-Generation Onion Router," *USENIX Security Symposium*, 2004.

[3] S. Burnett and N. Feamster, "Encore: Lightweight Measurement of Web Censorship with Cross-Origin Requests," *ACM SIGCOMM*, 2015.

[4] K. Ermoshina, F. Musiani, and H. Halpin, "End-to-End Encrypted Messaging Protocols: An Overview," *F. Bagnoli et al. (eds.), INSCI 2016*, LNCS, vol. 9934, 2016.

[5] Protocol Labs, "libp2p: A Modular Network Stack," https://libp2p.io/, 2023.

[6] S. Nakamoto, "Bitcoin: A Peer-to-Peer Electronic Cash System," 2008.

[7] D. J. Bernstein and T. Lange, "SafeCurves: Choosing Safe Curves for Elliptic-Curve Cryptography," https://safecurves.cr.yp.to/, 2014.

[8] A. J. Menezes, P. C. van Oorschot, and S. A. Vanstone, *Handbook of Applied Cryptography*, CRC Press, 1996.

[9] J. Warren, "Bitmessage: A Peer-to-Peer Message Authentication and Delivery System," 2012.

[10] Loki Foundation, "Session: A Model for End-to-End Encrypted Conversations with Minimal Metadata Leakage," *Whitepaper*, 2020.

[11] Status.im, "Status: A Mobile Ethereum OS," https://status.im/whitepaper.pdf, 2017.

[12] D. J. Bernstein, "Curve25519: New Diffie-Hellman Speed Records," *Public Key Cryptography – PKC 2006*, LNCS, vol. 3958, 2006.

[13] D. J. Bernstein, "A State-of-the-Art Diffie-Hellman Function," https://cr.yp.to/ecdh.html, 2006.

[14] D. J. Bernstein, N. Duif, T. Lange, P. Schwabe, and B.-Y. Yang, "High-Speed High-Security Signatures," *Journal of Cryptographic Engineering*, vol. 2, no. 2, pp. 77-89, 2012.

[15] C. Boyd and A. Mathuria, *Protocols for Authentication and Key Establishment*, Springer, 2003.

[16] H. Krawczyk, "The Order of Encryption and Authentication for Protecting Communications (Or: How Secure Is SSL?)," *CRYPTO 2001*, LNCS, vol. 2139, 2001.

[17] H. Krawczyk and P. Eronen, "HMAC-based Extract-and-Expand Key Derivation Function (HKDF)," RFC 5869, 2010.

[18] D. J. Bernstein, "ChaCha, a Variant of Salsa20," *SASC 2008*, 2008.

[19] M. Marlinspike and T. Perrin, "The Double Ratchet Algorithm," *Signal Specifications*, 2016.

[20] J. Bankoski et al., "VP9 Bitstream & Decoding Process Specification," *Google*, 2016.

[21] R. Dingledine, N. Mathewson, and P. Syverson, "Tor: The Second-Generation Onion Router," *USENIX Security*, 2004.

[22] A. Johnston and D. Burnett, *WebRTC: APIs and RTCWEB Protocols of the HTML5 Real-Time Web*, Digital Codex LLC, 2014.

[23] W3C, "Decentralized Identifiers (DIDs) v1.0," https://www.w3.org/TR/did-core/, 2022.

[24] B. Blanchet, "Modeling and Verifying Security Protocols with the Applied Pi Calculus and ProVerif," *Foundations and Trends in Privacy and Security*, vol. 1, no. 1–2, 2016.

---

## License

MIT License

## Authors

- Nilesh Chakraborty

## Acknowledgments

This work builds upon foundational research in distributed systems, cryptography, and blockchain technology. We acknowledge the contributions of the open-source community, particularly the developers of the `cryptography`, `websockets`, and `click` Python libraries.
