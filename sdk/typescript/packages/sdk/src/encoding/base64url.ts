/**
 * Base64URL encoding/decoding utilities.
 * Compliant with RFC 4648 with no padding.
 */

const ENC = {
    '+': '-',
    '/': '_',
    '=': ''
} as const;

const DEC = {
    '-': '+',
    '_': '/'
} as const;

export function encodeBase64Url(input: Uint8Array): string {
    // Convert bytes to standard base64 first
    let base64 = '';
    const len = input.length;
    for (let i = 0; i < len; i += 3) {
        const b1 = input[i];
        const b2 = i + 1 < len ? input[i + 1] : 0;
        const b3 = i + 2 < len ? input[i + 2] : 0;

        const triplet = (b1 << 16) | (b2 << 8) | b3;

        base64 += btoaString((triplet >> 18) & 0x3F);
        base64 += btoaString((triplet >> 12) & 0x3F);
        if (i + 1 < len) base64 += btoaString((triplet >> 6) & 0x3F);
        if (i + 2 < len) base64 += btoaString(triplet & 0x3F);
    }

    // Replace chars for URL safety and strip padding
    return base64.replace(/[+/=]/g, (m) => ENC[m as keyof typeof ENC] || '');
}

function btoaString(index: number): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
    return chars[index];
}

export function decodeBase64Url(input: string): Uint8Array {
    // Restore padding and standard chars
    let base64 = input.replace(/[-_]/g, (m) => DEC[m as keyof typeof DEC] || '');
    while (base64.length % 4) {
        base64 += '=';
    }

    // Decode standard base64
    // We avoid atob() to be purely functional and cross-platform safe without dom lib reliance
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

    // Create lookup table
    const lookup = new Uint8Array(256);
    for (let i = 0; i < chars.length; i++) lookup[chars.charCodeAt(i)] = i;

    const len = base64.length;
    let bufferLength = len * 0.75;
    if (base64[len - 1] === '=') {
        bufferLength--;
        if (base64[len - 2] === '=') bufferLength--;
    }

    const bytes = new Uint8Array(bufferLength);
    let p = 0;
    let encoded1, encoded2, encoded3, encoded4;

    for (let i = 0; i < len; i += 4) {
        encoded1 = lookup[base64.charCodeAt(i)];
        encoded2 = lookup[base64.charCodeAt(i + 1)];
        encoded3 = lookup[base64.charCodeAt(i + 2)];
        encoded4 = lookup[base64.charCodeAt(i + 3)];

        bytes[p++] = (encoded1 << 2) | (encoded2 >> 4);
        if (encoded3 !== 64) bytes[p++] = ((encoded2 & 15) << 4) | (encoded3 >> 2);
        if (encoded4 !== 64) bytes[p++] = ((encoded3 & 3) << 6) | (encoded4 & 63);
    }

    return bytes;
}
