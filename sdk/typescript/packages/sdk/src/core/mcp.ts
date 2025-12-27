import { canonicalize } from '../encoding/canonical_json.js';
import { sha256 } from '../crypto/sha256.js';

/**
 * Compute MCP Request Hash.
 * hash = sha256(canonical_json(mcp_request))
 * Output: Hex string (to match strict vectors).
 */
export async function computeRequestHash(request: unknown): Promise<string> {
    const canon = canonicalize(request);
    const hash = await sha256(canon);
    return Array.from(hash)
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

/**
 * Compute MCP Response Hash.
 * hash = sha256(canonical_json(mcp_response))
 * Output: Hex string.
 */
export async function computeResponseHash(response: unknown): Promise<string> {
    const canon = canonicalize(response);
    const hash = await sha256(canon);
    return Array.from(hash)
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

export function canonicalizeMcpRequest(request: unknown): Uint8Array {
    return canonicalize(request);
}
