import { canonicalize } from '../encoding/canonical_json.js';
import { encodeBase64Url, decodeBase64Url } from '../encoding/base64url.js';
import { sign as signEd25519, verify as verifyEd25519 } from '../crypto/ed25519.js';
import { Capability } from './capability.js';

export type McpMessageType = 'MCP_MESSAGE';
export type McpResponseType = 'MCP_RESPONSE';

export interface McpMessageFrame {
    type: McpMessageType;
    protocol_version: string;
    session_id: string;
    correlation_id: string;
    peer_id: string;
    issued_at: number;
    request_hash: string;
    tool: string;
    method: string;
    capability_hash: string;
    capability?: Capability;
    sig?: string;
}

export interface McpResponseFrame {
    type: McpResponseType;
    protocol_version: string;
    session_id: string;
    correlation_id: string;
    peer_id: string;
    issued_at: number;
    response_hash: string;
    tool: string;
    method: string;
    result_code: 'OK' | 'DENY' | 'ERROR';
    denial_reason?: string;
    mcp_id?: string;
    sig?: string;
}

const MCP_MESSAGE_FIELDS = new Set([
    'type', 'protocol_version', 'session_id', 'correlation_id', 'peer_id',
    'issued_at', 'request_hash', 'tool', 'method', 'capability_hash', 'capability', 'sig'
]);

const MCP_RESPONSE_FIELDS = new Set([
    'type', 'protocol_version', 'session_id', 'correlation_id', 'peer_id',
    'issued_at', 'response_hash', 'tool', 'method', 'result_code', 'denial_reason', 'mcp_id', 'sig'
]);

export function validateFrameStrict(frame: Record<string, unknown>): void {
    const type = frame['type'];
    if (type === 'MCP_MESSAGE') {
        for (const key of Object.keys(frame)) {
            if (!MCP_MESSAGE_FIELDS.has(key)) {
                throw new Error(`MCP_MESSAGE Frame Strictness: Unknown field '${key}' rejected`);
            }
        }
    } else if (type === 'MCP_RESPONSE') {
        for (const key of Object.keys(frame)) {
            if (!MCP_RESPONSE_FIELDS.has(key)) {
                throw new Error(`MCP_RESPONSE Frame Strictness: Unknown field '${key}' rejected`);
            }
        }
    } else {
        throw new Error(`Unknown frame type: ${type}`);
    }
}

export async function signFrame<T extends McpMessageFrame | McpResponseFrame>(frame: Omit<T, 'sig'>, privateKey: Uint8Array): Promise<T> {
    const contentCanonical = canonicalize(frame);
    const sigBytes = await signEd25519(contentCanonical, privateKey);
    const sig = encodeBase64Url(sigBytes);
    return { ...frame, sig } as T;
}

export async function verifyFrame(frame: McpMessageFrame | McpResponseFrame, publicKey: Uint8Array): Promise<boolean> {
    // Enforce strictness before verifying?
    // Yes, "Frames are strict: unknown top-level frame fields are rejected".
    // Note: This relies on the runtime object having extra keys if deserialized from JSON that had them.
    // Ideally pure verification function just takes object.
    validateFrameStrict(frame as unknown as Record<string, unknown>);

    if (!frame.sig) return false;

    const content = { ...frame };
    delete content.sig;

    const contentCanonical = canonicalize(content);
    const sigBytes = decodeBase64Url(frame.sig);

    return verifyEd25519(sigBytes, contentCanonical, publicKey);
}
