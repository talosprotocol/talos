import { McpMessageFrame, signFrame, verifyFrame } from './frames.js';
import { Capability } from './capability.js';

// Envelope in v1 IS essentially the MCP_MESSAGE frame
export const createEnvelope = signFrame;
export const verifyEnvelope = verifyFrame;

// Helper to construct envelope data object
export function createEnvelopeContent(
    sessionId: string,
    correlationId: string,
    peerId: string,
    requestHash: string,
    tool: string,
    method: string,
    capabilityHash: string,
    capability?: Capability
): Omit<McpMessageFrame, 'sig'> {
    return {
        type: 'MCP_MESSAGE',
        protocol_version: '1',
        session_id: sessionId,
        correlation_id: correlationId,
        peer_id: peerId,
        issued_at: Math.floor(Date.now() / 1000),
        request_hash: requestHash,
        tool: tool,
        method: method,
        capability_hash: capabilityHash,
        capability: capability
    };
}
