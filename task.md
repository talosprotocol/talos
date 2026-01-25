# Talos Project Plan

# [Priority 1] Dashboard Stop-Ship Execution (Local Helper Arch)

## Phase 0: Contracts (Blocking)
- [ ] Create `schemas/setup/v1` in `talos-contracts` <!-- id: 12 -->
    - [x] `job_create.schema.json`
    - [x] `job_event.schema.json`
    - [x] `recipe.schema.json`
    - [x] Create `agent_register_request.schema.json`
    - [x] Create `agent_register_response.schema.json`
    - [x] Create `agent_poll_request.schema.json`
    - [x] Create `agent_poll_response.schema.json`
    - [x] Create `agent_heartbeat.schema.json`
    - [x] Create `job_cancel.schema.json`
    - [x] Create `job_snapshot.schema.json`
- [ ] Create Pinned    - [x] Create `recipes/v1/manifest.json` with strict schema
- [ ] Register new schemas in manifest <!-- id: 13 -->

- [ ] Register new schemas in manifest <!-- id: 13 -->

- [ ] Check if `site/dashboard` needs setup (ensure submodule is active) <!-- id: 21 -->
- [x] Implement Dashboard Pairing Gates (Require non-default creds, Auth Secret) <!-- id: 22 -->
- [x] Implement Dashboard Setup API (Postgres/Drizzle) <!-- id: 23 -->

## Phase 1: Local Setup Helper
- [x] Scaffold `tools/setup-helper` <!-- id: 14 -->
- [x] Implement Local Manifest Verification (Self-pinned, SHA-256) <!-- id: 24 -->
- [x] Implement Auth & Polling Loop (with Lease state) <!-- id: 16 -->
- [x] Implement Recipe executor with Symlink/TOCTOU Jail <!-- id: 15 -->

## Phase 2: Dashboard Control Plane
- [x] Implement `SqliteJobStore` (Postgres/Drizzle) <!-- id: 20 -->
- [x] Implement Control Plane API (`/api/setup/*`) <!-- id: 17 -->
- [x] Implement `SetupWizard` & `AgentConnection` UI <!-- id: 18 -->

# [Priority 2] UCP Support (Phase 0)
- [x] Analyze UCP requirements and existing MCP connector <!-- id: 4 -->
- [x] Create UCP implementation plan (Corrected) <!-- id: 5 -->
- [x] Add `talos-ucp-connector` submodule to `services/ucp-connector` <!-- id: 11 -->
- [x] Add UCP schemas to `talos-contracts` (Phase 0) <!-- id: 8 -->
- [x] Add UCP test vectors to `talos-contracts` (Phase 0) <!-- id: 9 -->
- [x] Implement UCP Connector Service (Phase 1) <!-- id: 10 -->
- [x] **Phase 2:** Payment Handlers via `WalletProvider` (Started)
