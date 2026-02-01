# Talos Protocol Documentation

Welcome to the Talos Protocol documentation! This documentation is organized into logical categories for easy navigation.

## Quick Links

- 🚀 [Getting Started](#getting-started) - New to Talos? Start here!
- 📖 [Guides](#guides) - Step-by-step how-to guides
- 🏗️ [Architecture](#architecture) - System design and structure
- ⭐ [Features](#features) - Core capabilities
- 💻 [SDK](#sdk) - Client libraries and integration
- 🔌 [API](#api) - API reference
- 🔒 [Security](#security) - Security documentation
- 🧪 [Testing](#testing) - Testing guides
- 📚 [Reference](#reference) - Glossary and comparisons
- 🔬 [Research](#research) - Whitepaper, roadmap, future work
- 💼 [Business](#business) - Go-to-market and enterprise
- 🌐 [Network Protocols](#network-protocols) - Communication protocols
- ⚙️ [Configuration Reference](#configuration-reference) - Configuration schemas

---

## Getting Started

New to Talos? Start with these guides:

- **[Talos in 60 Seconds](getting-started-talos-60-seconds)** - Ultra-quick overview
- **[Mental Model](getting-started-mental-model)** - Understand the core concepts
- **[Quickstart Guide](getting-started-quickstart)** - Get up and running
- **[Simple Guide](getting-started-simple-guide)** - Step-by-step tutorial
- **[One-Command Demo](getting-started-one-command-demo)** - Try it now

## Guides

Practical how-to guides for common tasks:

- **[Deployment](guides-deployment)** - Production deployment guide
- **[Development](guides-development)** - Local development setup
- **[Production Hardening](guides-production-hardening)** - Production best practices
- **[Hardening Guide](guides-hardening-guide)** - Security hardening
- **[Runbook (Non-Technical)](guides-runbook-non-technical)** - Operations guide
- **[Error Troubleshooting](guides-error-troubleshooting)** - Common issues

## Architecture

System design and technical architecture:

- **[Overview](architecture-overview)** - High-level architecture
- **[Simplified View](architecture-simplified)** - Architecture for beginners
- **[Infrastructure](architecture-infrastructure)** - Infrastructure design
- **[Wire Format](architecture-wire-format)** - Protocol wire format
- **[Protocol Guarantees](architecture-protocol-guarantees)** - What Talos guarantees
- **[Threat Model](architecture-threat-model)** - Security threat model

## Features

Core features and capabilities:

### Identity & Authentication

- [Agent Identity](features-identity-agent-identity)
- [DIDs with DHT](features-identity-dids-dht)
- [Key Management](features-identity-key-management)

### Authorization

- [Access Control](features-authorization-access-control)
- [Capability Authorization](features-authorization-capability-authorization)
- [Agent Capabilities](features-authorization-agent-capabilities)

### Messaging

- [A2A Channels](features-messaging-a2a-channels)
- [Double Ratchet](features-messaging-double-ratchet)
- [Group Messaging](features-messaging-group-messaging)
- [File Transfer](features-messaging-file-transfer)

### Observability

- [Audit Scope](features-observability-audit-scope)
- [Audit Use Cases](features-observability-audit-use-cases)
- [Audit Explorer](features-observability-audit-explorer)
- [Observability](features-observability-observability)

### Operations

- [Adaptive Budgets](features-operations-adaptive-budgets)
- [Secrets Rotation](features-operations-secrets-rotation)
- [Multi-Region](features-operations-multi-region)
- [Global Load Balancing](features-operations-global-load-balancing)

### Integrations

- [MCP Integration](features-integrations-mcp-integration)
- [MCP Cookbook](features-integrations-mcp-cookbook)
- [MCP Proof Flow](features-integrations-mcp-proof-flow)
- [Framework Integrations](features-integrations-framework-integrations)

## SDK

Client libraries and integration guides:

- **[Python SDK](sdk-python-sdk)** - Python client library
- **[TypeScript SDK](sdk-typescript-sdk)** - TypeScript/JavaScript library
- **[A2A SDK Guide](sdk-a2a-sdk-guide)** - Agent-to-Agent messaging guide
- **[SDK Integration](sdk-sdk-integration)** - Integration guide
- **[SDK Ergonomics](sdk-sdk-ergonomics)** - SDK design principles
- **[Usage Examples](sdk-usage-examples)** - Code examples
- **[Examples](sdk-examples)** - More examples

## API

API documentation and reference:

- **[API Reference](api-api-reference)** - Complete API reference
- **[Schemas](api-schemas)** - JSON schema documentation

## Security

Security documentation and best practices:

- **[Cryptography](security-cryptography)** - Cryptographic primitives
- **[Security Properties](security-security-properties)** - Security guarantees
- **[Mathematical Proof](security-mathematical-proof)** - Formal security proof
- **[Validation Engine](security-validation-engine)** - Input validation
- **[Security Dashboard](security-security-dashboard)** - Security monitoring

## Testing

Testing guides and documentation:

- **[Testing Guide](testing-testing)** - How to test Talos
- **[Benchmarks](testing-benchmarks)** - Performance benchmarks
- **[Test Manifests](testing-test-manifests)** - Test manifest format
- **[Compatibility Matrix](testing-compatibility-matrix)** - Platform compatibility

## Network Protocols

- [Talos Overlays](file:---Users-nileshchakraborty-workspace-talos-docs-protocols-overlays): Secure mesh networking protocol.

## Configuration Reference

- [Core Schemas](file:///Users/nileshchakraborty/workspace/talos/contracts/schemas/config/v1): JSON schemas for all configuration objects.

## Reference

Reference material and comparisons:

- **[Glossary](reference-glossary)** - Terms and definitions
- **[Alternatives Comparison](reference-alternatives-comparison)** - How Talos compares
- **[Failure Modes](reference-failure-modes)** - Known failure modes
- **[Non-Goals](reference-non-goals)** - What Talos doesn't do
- **[Decision Log](reference-decision-log)** - Design decisions

## Research

Research papers, roadmap, and future work:

- **[Whitepaper](research-whitepaper)** - Technical whitepaper
- **[Roadmap](research-roadmap)** - Product roadmap
- **[Future Improvements](research-future-improvements)** - Planned features
- **[Agents Research](research-agents)** - Agent research
- **[MVP Design](research-mvp-design)** - MVP design document
- **[Blockchain](research-blockchain)** - Blockchain integration research  
- **[ICP](research-icp)** - Internet Computer Protocol
- **[Light Client](research-light-client)** - Light client design

## Business

Go-to-market and enterprise documentation:

- **[GTM Plan](business-gtm-plan)** - Go-to-market strategy
- **[Why Talos Wins](business-why-talos-wins)** - Competitive advantages
- **[Enterprise Performance](business-enterprise-performance)** - Enterprise capabilities
- **[Agent Lifecycle](business-agent-lifecycle)** - Agent management

---

## Templates

Documentation templates for contributors:

- [API Template](templates-api-template)
- [Contributing Template](templates-contributing-template)
- [README Template](templates-readme-template)
- [README Checklist](templates-readme-checklist)

---

## Contributing

See our [contributing guidelines](templates-contributing-template) for how to contribute to this documentation.

## License

This documentation is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.
