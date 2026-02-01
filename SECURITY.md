# Talos Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 5.15.x  | ✅ Yes    |
| 3.x     | ❌ No     |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

### Contact

Email: [reach@talosprotocol.com](mailto:reach@talosprotocol.com)

### What to Include

1. Type of vulnerability
2. Full path to source file(s) with issue
3. Location in code (tag/branch/commit or URL)
4. Step-by-step reproduction instructions
5. Proof-of-concept or exploit code (if possible)
6. Impact assessment

### Response Timeline

| Action             | Timeline    |
| ------------------ | ----------- |
| Acknowledgment     | 48 hours    |
| Initial assessment | 1 week      |
| Fix development    | 2-4 weeks   |
| Disclosure         | Coordinated |

### Safe Harbor

We consider security research conducted in accordance with this policy to be:

- Authorized
- Helpful to the project
- Protected from legal action

## Scope

### In Scope

- Talos protocol implementation
- Python SDK
- CLI tools
- Cryptographic operations
- Authentication/authorization

### Out of Scope

- Third-party dependencies (report upstream)
- Social engineering
- Physical attacks
- DoS attacks without payload

## Cryptography Notes

Talos uses:

- **Ed25519** for signatures (libsodium via cryptography library)
- **X25519** for key exchange
- **ChaCha20-Poly1305** for encryption
- **HKDF** for key derivation

All randomness uses `secrets` module (OS-level CSPRNG).

## Acknowledgments

We maintain a hall of fame for security researchers who responsibly disclose vulnerabilities:

_[No entries yet]_
