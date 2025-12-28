/**
 * Encodes a UTF-8 string to Base64URL (RFC 4648).
 * Compatible with Browser and Node.js environments.
 */
export function base64UrlEncode(data: Uint8Array): string {
    let b64: string;

    if (typeof window !== 'undefined' && typeof window.btoa === 'function') {
        // Browser
        const binaryStr = Array.from(data, (byte) => String.fromCharCode(byte)).join("");
        b64 = window.btoa(binaryStr);
    } else {
        // Node.js
        b64 = Buffer.from(data).toString('base64');
    }

    return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/**
 * Legacy wrapper for string input (compat only)
 */
export function base64urlEncodeUtf8(str: string): string {
    return base64UrlEncode(new TextEncoder().encode(str));
}

/**
 * Decodes Base64URL string to Uint8Array.
 * Throws if invalid.
 */
export function base64UrlDecodeToBytes(str: string): Uint8Array {
    // Convert Base64URL to Base64
    let b64 = str.replace(/-/g, '+').replace(/_/g, '/');
    // Pad
    while (b64.length % 4) {
        b64 += '=';
    }

    if (typeof window !== 'undefined' && typeof window.atob === 'function') {
        const binaryStr = window.atob(b64);
        const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) {
            bytes[i] = binaryStr.charCodeAt(i);
        }
        return bytes;
    } else {
        return Buffer.from(b64, 'base64');
    }
}
