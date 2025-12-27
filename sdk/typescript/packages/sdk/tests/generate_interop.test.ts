import { describe, it } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { fromSeed, signCapability, signFrame, createEnvelopeContent } from '../src/index.js';

const OUTPUT_PATH = path.resolve(__dirname, '../../../../../test_vectors/ts_generated/interop.json');

describe('Generate Interop Vectors', () => {
    it('Should generate signed artifacts for Python to verify', async () => {
        // 1. Setup deterministic keys (Seed = 32 bytes of 0x01)
        const seed = new Uint8Array(32).fill(1);
        const keyPair = fromSeed(seed);

        // 2. Capability
        const capContent = {
            v: "1",
            iss: "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK", // Example DID for seed 1? Or just arbitrary. Python verify script needs ONLY pubkey and signature/content.
            // We'll export public key too.
            sub: "did:web:example.com",
            scope: "read:files",
            iat: 1234567890,
            exp: 1234567890 + 3600
        };
        const cap = await signCapability(capContent, keyPair.privateKey);

        // 3. Frame
        const frameContent = createEnvelopeContent(
            "session-123",
            "corr-456",
            "peer-789",
            "aad459...", // arbitrary hash
            "read:files",
            "list",
            "bbccdd...", // arbitrary
            cap // Include cap
        );
        // Explicitly set timestamp to deterministic value if needed, but createEnvelopeContent sets Date.now().
        // We can override it.
        (frameContent as any).issued_at = 1234567890;

        const frame = await signFrame(frameContent, keyPair.privateKey);

        // 4. Output
        const output = {
            public_key_hex: Buffer.from(keyPair.publicKey).toString('hex'),
            capability: cap,
            frame: frame
        };

        fs.writeFileSync(OUTPUT_PATH, JSON.stringify(output, null, 2));
        console.log(`Generated interop vectors at ${OUTPUT_PATH}`);
    });
});
