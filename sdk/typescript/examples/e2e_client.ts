
import {
    TalosAgent,
    InMemoryKeyProvider,
    InMemoryCapabilityStore,
    signMcpRequest,
} from '@talos-protocol/client';
import { fromSeed, signCapability, Capability } from '@talos-protocol/sdk';

// Mock dependencies
const SEED = new Uint8Array(32).fill(1); // Deterministic seed
const AGENT_ID = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK";
const SESSION_ID = "session-123";


async function main() {
    // 1. Setup Agent
    const keyProvider = new InMemoryKeyProvider(SEED); // Private Key derived from seed
    const capStore = new InMemoryCapabilityStore();

    const agent = new TalosAgent(AGENT_ID, keyProvider, capStore);

    // 2. Create and Store a Capability
    // In a real flow, this comes from a "Grant" response. Here we self-issue for testing.
    const capContent: Omit<Capability, 'sig'> = {
        v: "1",
        iss: AGENT_ID, // Self-issued for test? Or mock issuer.
        sub: AGENT_ID,
        scope: "files/read",
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 3600
    };

    // Sign it with same key (self-signed) for simplicity, or we mock issuer verification in Python.
    // Validation script will check signature against the public key we verify with.
    const kp = fromSeed(SEED);
    const capability = await signCapability(capContent, kp.privateKey);

    await capStore.put(capability);

    // 3. Create MCP Request (JSON-RPC)
    const mcpRequest = {
        jsonrpc: "2.0",
        id: 1,
        method: "files/read",
        params: {
            path: "/etc/hosts"
        }
    };

    // 4. Sign Request (Create Envelope Frame)
    const frame = await signMcpRequest(
        agent,
        mcpRequest,
        SESSION_ID,
        "corr-1", // correlation_id
        "files", // tool name (derived from method or explicit)
        "read" // method name
    );

    // 5. Output
    // eslint-disable-next-line
    console.log(JSON.stringify({
        request: mcpRequest,
        frame: frame,
        public_key_hex: Buffer.from(kp.publicKey).toString('hex')
    }, null, 2));
}

main().catch(console.error);
