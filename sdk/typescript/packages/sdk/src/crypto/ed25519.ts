import * as ed from '@noble/ed25519';
import { sha512 } from '@noble/hashes/sha512';

// Configure sha512 sync for @noble/ed25519 v2
ed.etc.sha512Sync = (...m) => sha512(ed.etc.concatBytes(...m));

export interface KeyPair {
    publicKey: Uint8Array;
    privateKey: Uint8Array;
}

/**
 * Generate a random Ed25519 keypair.
 */
export function generateKeyPair(): KeyPair {
    const privateKey = ed.utils.randomPrivateKey();
    const publicKey = ed.getPublicKey(privateKey);
    return { publicKey, privateKey };
}

/**
 * Generate a deterministic Ed25519 keypair from a 32-byte seed.
 * Strict compliance for vectors.
 */
export function fromSeed(seed: Uint8Array): KeyPair {
    if (seed.length !== 32) {
        throw new Error(`Seed must be 32 bytes, got ${seed.length}`);
    }
    // Ed25519 private key is effectively the seed in many implementations.
    // @noble/ed25519 treats private key as 32 bytes.
    const privateKey = seed;
    const publicKey = ed.getPublicKey(privateKey);
    return { publicKey, privateKey };
}

/**
 * Sign message with Ed25519.
 */
export async function sign(message: Uint8Array, privateKey: Uint8Array): Promise<Uint8Array> {
    return ed.signAsync(message, privateKey);
}

/**
 * Verify signature with Ed25519.
 */
export async function verify(signature: Uint8Array, message: Uint8Array, publicKey: Uint8Array): Promise<boolean> {
    return ed.verifyAsync(signature, message, publicKey);
}
