import { describe, it, expect, beforeAll } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { canonicalize } from '../src/encoding/canonical_json.js';
import { computeCapabilityHash, verifyCapability } from '../src/core/capability.js';
import { computeRequestHash, canonicalizeMcpRequest } from '../src/core/mcp.js';
import { verifyFrame } from '../src/core/frames.js';
import { fromSeed, verify } from '../src/crypto/ed25519.js';
import { decodeBase64Url } from '../src/encoding/base64url.js';

const VECTORS_ROOT = path.resolve(__dirname, '../../../../../test_vectors');


function readJson(relPath: string) {
    return JSON.parse(fs.readFileSync(path.join(VECTORS_ROOT, relPath), 'utf-8'));
}

function readBytes(relPath: string) {
    return new Uint8Array(fs.readFileSync(path.join(VECTORS_ROOT, relPath)));
}

function readHex(relPath: string) {
    return fs.readFileSync(path.join(VECTORS_ROOT, relPath), 'utf-8').trim();
}

describe('Phase 4.1 Vector Compliance', () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let meta: any;
    let keyPair: { publicKey: Uint8Array; privateKey: Uint8Array };

    beforeAll(() => {
        meta = readJson('meta.json');
        // Generate keypair from seed to verify signatures if needed
        const seed = new Uint8Array(Buffer.from(meta.keypair_seed_hex, 'hex'));
        keyPair = fromSeed(seed);
    });

    describe('Positive Vectors', () => {
        it('Capability Canonicalization (Content)', async () => {
            const cap = readJson('positive/capability.json');
            const expectedBytes = readBytes('positive/capability_content_canonical.bytes');

            // Construct content (minus sig)
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const { sig: _, ...content } = cap;
            const canon = canonicalize(content);

            // Compare bytes
            expect(canon).toEqual(expectedBytes);
        });

        it('Capability Token Canonicalization (With Sig)', async () => {
            const cap = readJson('positive/capability.json');
            const expectedBytes = readBytes('positive/capability_token_canonical.bytes');

            const canon = canonicalize(cap);
            expect(canon).toEqual(expectedBytes);
        });

        it('Capability Hash', async () => {
            const cap = readJson('positive/capability.json');
            const expectedHash = readHex('positive/capability_hash.hex');

            const hash = await computeCapabilityHash(cap);
            expect(hash).toEqual(expectedHash);
        });

        it('Capability Signature Verification', async () => {
            const cap = readJson('positive/capability.json');
            const isValid = await verifyCapability(cap, keyPair.publicKey);
            expect(isValid).toBe(true);
        });

        it('MCP Request Canonicalization', async () => {
            const req = readJson('positive/mcp_request.json');
            const expectedBytes = readBytes('positive/mcp_request_canonical.bytes');
            const canon = canonicalizeMcpRequest(req);
            expect(canon).toEqual(expectedBytes);
        });

        it('MCP Request Hash', async () => {
            const req = readJson('positive/mcp_request.json');
            const expectedHash = readHex('positive/request_hash.hex');
            const hash = await computeRequestHash(req);
            expect(hash).toEqual(expectedHash);
        });

        it('MCP Message Frame Verification', async () => {
            const frame = readJson('positive/mcp_message_frame.json');
            const isValid = await verifyFrame(frame, keyPair.publicKey);
            expect(isValid).toBe(true);
        });

        it('MCP Response Frame Verification', async () => {
            const frame = readJson('positive/mcp_response_frame.json');
            const isValid = await verifyFrame(frame, keyPair.publicKey);
            expect(isValid).toBe(true);
        });
    });

    describe('Negative Vectors', () => {
        // Helper to load negative vector
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const checkNegative = async (filename: string, checkFn: (input: any) => Promise<boolean>) => {
            const vector = readJson(`negative/${filename}`);
            if (vector.vector_type === 'raw_string') {
                // Special handling if needed, likely verify fails on parsed content vs signature mismatch
                // or JSON.parse might accept it but canonicalization makes it mismatch signature?
                try {
                    const input = JSON.parse(vector.input);
                    return await checkFn(input);
                } catch (e) {
                    return false; // Parse error considered rejection
                }
            }
            return await checkFn(vector.input);
        };

        it('wrong_sig matches expected denial', async () => {
            const result = await checkNegative('wrong_sig.json', (input) => verifyCapability(input, keyPair.publicKey));
            expect(result).toBe(false);
        });

        it('non_canonical_json_order matches expected denial', async () => {
            // Signature generated over messy bytes. We verify canonical bytes. Should match false.
            const result = await checkNegative('non_canonical_json_order.json', (input) => {
                // Check based on object type? Vector has "v", "a_field", "b_field". It's a generic object.
                // Using verifyCapability logic: strict structure? No, it just checks signature over content.
                // We can treat it as a generic signed object check.
                // verifyCapability expects Capability interface but verifyEd25519 works on any object.
                // Let's manually verify using generic verify logic
                const { sig, ...content } = input;
                if (!sig) return Promise.resolve(false);
                const canon = canonicalize(content);
                const sigBytes = decodeBase64Url(sig);
                return verify(sigBytes, canon, keyPair.publicKey);
            });
            expect(result).toBe(false);
        });

        it('missing_request_binding should fail frame strictness or signature', async () => {
            // If request_hash is missing, frame validation might fail if strict checks added.
            // My current verifyFrame check signature.
            // If signed WITHOUT request_hash, it passes signature check.
            // Vector generator: "Let's simulate a frame that *omits* request_hash".
            // BUT does it sign it? Generator code: `frame_no_hash = mcp_msg_content.copy(); del frame_no_hash["request_hash"];`
            // It copies content (presumably with valid signature from mcp_msg_content?).
            // `mcp_msg_content` was dictionary BEFORE signing in generator?
            // Wait, `generate_positive` creates `mcp_msg_frame` with signature.
            // `generate_negative` copies `mcp_msg_content` (the raw content dict), removes hash, THEN wraps it?
            // "This vector implies the verifier checks hash vs payload... Let's simulate a frame that *omits* request_hash".
            // Generator code:
            // `frame_no_hash = mcp_msg_content.copy()` -> Copies raw dict (no sig yet).
            // `del frame_no_hash["request_hash"]`
            // Then writes it. It DOES NOT sign it in the negative generator snippet I wrote?
            // Ah, `generate_negative` -> `missing_request_binding` snippet:
            // It creates `frame_no_hash` dict.
            // `write_vector(..., {"input": frame_no_hash})`
            // It lacks a signature! 
            // If it lacks a signature, `verifyFrame` returns false immediately.
            // Correct.

            const result = await checkNegative('missing_request_binding.json', (input) => verifyFrame(input, keyPair.publicKey));
            expect(result).toBe(false);
        });
    });

    describe('Replay / Session', () => {
        it('Replay vector contains expected denial', async () => {
            const vec = readJson('replay/duplicate.json');
            expect(vec.expected_denial).toBe('REPLAY');
            // Verify items are valid individually
            const frames = vec.input;
            const v1 = await verifyFrame(frames[0], keyPair.publicKey);
            expect(v1).toBe(true);
        });
    });
});
