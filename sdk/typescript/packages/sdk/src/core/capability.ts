import { canonicalize } from '../encoding/canonical_json.js';
import { encodeBase64Url, decodeBase64Url } from '../encoding/base64url.js';
import { sha256 } from '../crypto/sha256.js';
import { sign as signEd25519, verify as verifyEd25519 } from '../crypto/ed25519.js';
import { bytesToUtf8 } from '../encoding/bytes.js';

export interface Capability {
    v: string; // Version "1"
    iss: string; // Issuer DID
    sub: string; // Subject DID
    scope: string;
    constraints?: Record<string, unknown>;
    iat: number;
    exp: number;
    delegatable?: boolean;
    delegation_chain?: string[]; // Encoded caps usually? Or just signatures? Spec says "repeated bytes delegation_chain" in protobuf, "delegation_chain": [] in JSON.
    sig?: string; // Signature (base64url)
}

/**
 * Compute Capability Hash (Identity).
 * hash = sha256(canonical_json(capability_with_signature))
 */
export async function computeCapabilityHash(cap: Capability): Promise<string> {
    const canon = canonicalize(cap);
    const hash = await sha256(canon);
    // Hash is usually hex in vectors? Protocol says "Binary fields: base64url".
    // Vectors use hex for readability filenames but internally?
    // Protocol 1.1 "Binary Encoding (Hot Path)" says request_hash is bytes.
    // JSON structure usually uses hex for hashes in many systems but Talos says "Binary fields = base64url".
    // Wait, let's check vectors generation script.
    // sha256_hash returns hex.
    // But plan said "Binary fields = base64url without padding" in "Canonicalization Limits".
    // Does that apply to hashes representing identity strings?
    // Protocol says "Binary Encoding... request_hash = 5; // 32 bytes".
    // In JSON "request_hash": "<hex>" ??
    // Let's check the vector generator I wrote. 
    // It uses `sha256_hash(data).hexdigest()`. So it writes HEX to the JSON vectors.
    // I should stick to HEX for hashes if that's what vectors produced, or verify what I wrote.
    // I wrote `write_vector(..., req_hash)` where req_hash is hexdigest.
    // So hashes in JSON are HEX strings.

    // Wait, `meta.json` says `hash_alg: "sha256"`. 
    // If I want to match vectors, I must produce HEX.
    // But user plan says "Binary fields = base64url".
    // This is a conflict. 
    // "Binary fields = base64url" usually applies to `content`, `signature`, `nonce`.
    // Hashes are often hex.
    // Given I generated vectors with Hex, I MUST support Hex for hashes to match the "byte perfect" check against values I generated?
    // Or did I only write the hash to a separate file `capability_hash.hex`?
    // AND `mcp_msg_frame` includes `request_hash`.
    // In `generic_positive`:
    // `mcp_msg_content = { ..., "request_hash": req_hash, ... }`
    // `req_hash` comes from `sha256_hash` which calls `hexdigest()`.
    // So the vectors use HEX for hashes in the JSON frames.
    // I will use HEX for hashes.

    // Helper for hex
    const hashHex = Array.from(hash)
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
    return hashHex;
}

export async function signCapability(cap: Omit<Capability, 'sig'>, privateKey: Uint8Array): Promise<Capability> {
    const contentCanonical = canonicalize(cap);
    const sigBytes = await signEd25519(contentCanonical, privateKey);
    const sig = encodeBase64Url(sigBytes);
    return { ...cap, sig } as Capability;
}

export async function verifyCapability(cap: Capability, publicKey: Uint8Array): Promise<boolean> {
    if (!cap.sig) return false;

    // Remove signature to get content
    const content = { ...cap };
    delete content.sig;

    const contentCanonical = canonicalize(content);
    const sigBytes = decodeBase64Url(cap.sig);

    return verifyEd25519(sigBytes, contentCanonical, publicKey);
}
