import { sha256 as nobleSha256 } from '@noble/hashes/sha256';

/**
 * Validates SHA-256 hash availability and computes strict SHA-256.
 * Uses WebCrypto if available (fastest), falls back to @noble/hashes (pure JS).
 */
export async function sha256(data: Uint8Array): Promise<Uint8Array> {
    // Use WebCrypto if available in environment (Browser / Node 19+)
    if (globalThis.crypto?.subtle) {
        try {
            const buffer = await globalThis.crypto.subtle.digest('SHA-256', data as BufferSource);
            return new Uint8Array(buffer);
        } catch {
            // Fallback to noble if WebCrypto fails or is restricted
        }
    }

    // Pure JS fallback
    return nobleSha256(data);
}
