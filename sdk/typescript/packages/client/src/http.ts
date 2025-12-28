import { TalosAgent } from './agent.js';
import {
    McpMessageFrame, McpResponseFrame,
    createEnvelopeContent,
    computeRequestHash,
    computeCapabilityHash,
    canonicalize,
    encodeBase64Url,
    verifyFrame
} from '@talos-protocol/sdk';

export async function signMcpRequest(
    agent: TalosAgent,
    request: unknown,
    sessionId: string,
    correlationId: string,
    tool: string,
    method: string
): Promise<McpMessageFrame> {
    const requestHash = await computeRequestHash(request);

    // Get capability
    const cap = await agent.capStore.get(tool, method);
    if (!cap) {
        throw new Error(`No capability found for ${tool}/${method}`);
    }

    const capHash = await computeCapabilityHash(cap);

    // Create frame content (unsigned)
    // Note: createEnvelopeContent takes arguments for constructing dict.
    // We explicitly include capability for now (stateless approach).
    const frameContent = createEnvelopeContent(
        sessionId,
        correlationId,
        agent.agentId,
        requestHash,
        tool,
        method,
        capHash,
        cap
    );

    // Canonicalize and Sign using Agent's provider
    const contentCanonical = canonicalize(frameContent);
    const sigBytes = await agent.keyProvider.sign(contentCanonical);
    const sig = encodeBase64Url(sigBytes);

    return { ...frameContent, sig } as McpMessageFrame;
}

export async function verifyMcpResponse(
    responseFrame: McpResponseFrame,
    serverPublicKey: Uint8Array
): Promise<boolean> {
    // Verify the frame signature
    // Note: verifyFrame in SDK uses verifyEd25519 which needs public key bytes.
    return verifyFrame(responseFrame, serverPublicKey);
}
