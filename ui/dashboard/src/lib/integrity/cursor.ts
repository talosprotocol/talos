// ui/dashboard/src/lib/integrity/cursor.ts
import { base64UrlEncode, base64UrlDecodeToBytes } from "../encoding/base64url";

export type CursorValidationReason = "CURSOR_MISMATCH" | "INVALID_FRAME";

export type CursorValidationResult =
    | { ok: true; derived: string }
    | { ok: false; derived: string; reason: CursorValidationReason };

function utf8Bytes(s: string): Uint8Array {
    return new TextEncoder().encode(s);
}

function isValidUnixSecondsInt(n: unknown): n is number {
    return typeof n === "number" && Number.isInteger(n) && n >= 0 && Number.isSafeInteger(n);
}

function unixSecondsToAscii(n: number): string {
    // base-10 ASCII digits, no whitespace. 
    // String(n) for an integer does exactly this.
    return String(n);
}

export function deriveCursor(timestamp: number, eventId: string): string {
    // v3.2 frozen constraints: timestamp is Unix seconds integer
    if (!isValidUnixSecondsInt(timestamp)) {
        throw new Error("INVALID_FRAME: timestamp must be unix seconds integer");
    }
    const ts = unixSecondsToAscii(timestamp);
    const plain = `${ts}:${eventId}`;
    return base64UrlEncode(utf8Bytes(plain));
}

export function validateCursor(event: { timestamp: unknown; event_id: unknown; cursor: unknown }): CursorValidationResult {
    // 1. Frame Check
    if (!isValidUnixSecondsInt(event.timestamp) || typeof event.event_id !== "string" || typeof event.cursor !== "string") {
        // If we can't even try to derive, we return invalid frame with empty derived? 
        // Or we try to derive with defaults? 
        // The snippet returns derived="" for INVALID_FRAME on input type error
        return { ok: false, derived: "", reason: "INVALID_FRAME" };
    }

    // 2. Decode Check (Optional but recommended in spec)
    try {
        base64UrlDecodeToBytes(event.cursor);
    } catch {
        // If cursor is not valid base64url, it's a frame error, 
        // but implies we calculate what it SHOULD be for logging?
        // Snippet says: catch -> derive -> return INVALID_FRAME
        const derived = deriveCursor(event.timestamp, event.event_id);
        return { ok: false, derived, reason: "INVALID_FRAME" };
    }

    // 3. Comparison
    const derived = deriveCursor(event.timestamp, event.event_id);
    if (event.cursor !== derived) {
        return { ok: false, derived, reason: "CURSOR_MISMATCH" };
    }

    return { ok: true, derived };
}
