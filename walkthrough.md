# Local Setup Helper Implementation Walkthrough

## Overview
This walkthrough details the implementation of the **Talos Local Setup Helper**, a secure "Control Plane" architecture that replaces the previous dashboard-integrated execution model. This design separates the **Dashboard (UI)** from the **privileged local executor (Helper)**, ensuring no remote code execution vulnerabilities.

## Architecture
- **Control Plane (`site/dashboard`)**: Managed UI, Job Store (Postgres/Drizzle), and API.
- **Agent (`tools/setup-helper`)**: Local Python daemon polling for jobs.
- **Contract (`talos-contracts`)**: Strict JSON schemas defining the protocol.

## Security Invariants Implemented
1.  **No Arbitrary Commands**: Recipes are allowlisted in `recipes/v1/manifest.json`.
2.  **Workspace Jail**: Helper enforces strict `SETUP_WORKSPACE_ROOT` confinement with symlink rejection (`tools/setup-helper/talos_setup_helper/jail.py`).
3.  **One-Way Trust**: Helper uses a **Self-Pinned Manifest** with SHA-256 digests (`tools/setup-helper/talos_setup_helper/manifest.py`).
4.  **Pairing Gates**: Dashboard Setup API is hard-gated behind `AUTH_SECRET` and Admin checks (`site/dashboard/src/lib/setup-gate.ts`).

## Component Details

### 1. Contracts & Manifests
-   **Schemas**: `contracts/schemas/setup/v1/*.schema.json`
-   **Manifest**: `contracts/recipes/v1/manifest.json` (Pinned Recipe List)
-   **Test Vectors**: `contracts/test_vectors/setup/v1/*.json` (Security Enforcement)

### 2. Local Setup Helper (`tools/setup-helper`)
-   **`cli.py`**: Entrypoint for `pair` and `start`.
-   **`auth.py`**: Manages secure token exchange and identity storage.
-   **`agent.py`**: Main event loop for long-polling the dashboard.
-   **`jail.py`**: Security core—enforces filesystem isolation.
-   **`manifest.py`**: Enforces trust by validating recipe digests against local pins.

### 3. Dashboard Control Plane (`site/dashboard`)
-   **Database**: Defines `setup_agents` and `setup_jobs` via Drizzle ORM (`src/db/schema.ts`).
-   **Security**: `verifySetupGates()` helper blocks access if insecure defaults are present.
-   **API Routes**:
    -   `POST /api/setup/agents/token`: Generates and stores pairing tokens in Postgres.
    -   `POST /api/setup/agents/register`: Validates token against DB and exchanges for agent credentials.
    -   `POST /api/setup/jobs`: Creates job records in `setup_jobs` table (status: queued).
    -   `POST /api/setup/agents/[id]/poll`: Atomically leases queued jobs to agents via DB transaction.

### 4. Setup UI (`site/dashboard/src/app/setup`)
-   **`Page.tsx`**: Main entrypoint hosting Connection and Wizard steps.
-   **`AgentConnection.tsx`**: UI to generate pairing tokens (calls new `pairing_tokens` DB API).
-   **`SetupWizard.tsx`**: UI to define project args and queue jobs (calls new `setup_jobs` DB API).
-   **`Components/UI`**: Scaffolded Shadcn Button, Card, Input, Label, Alert.

## Verification
-   **Security Tests**: `tools/setup-helper/tests/test_security.py` passes.
-   **Control Plane**: API routes use real Drizzle/Postgres persistence (No Mocks).
-   **Frontend**: UI components wired to real endpoints.

## Next Steps
-   Run the Control Plane and Helper to perform an end-to-end test.

