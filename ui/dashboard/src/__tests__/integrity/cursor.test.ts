import { describe, it, expect } from "vitest";
import { deriveCursor, validateCursor } from "../../lib/integrity/cursor";
import { AuditEvent } from "../../lib/data/schemas";

describe("Cursor Integrity (v3.2 Frozen)", () => {

    // Test Vector 1: Basic Derivation
    it("should derive correct base64url cursor for standard inputs", () => {
        const timestamp = 1700000000;
        const eventId = "evt_001";
        // "1700000000:evt_001" 
        // Base64: MTcwMDAwMDAwMDZldnRfMDAx (approx)
        // Let's rely on the function logic matches the spec: base64url(utf8(ts:id))

        const cursor = deriveCursor(timestamp, eventId);

        // Manual verification:
        // "1700000000:evt_001" -> Buffer -> Base64URL
        const manual = Buffer.from(`${timestamp}:${eventId}`).toString('base64url');
        expect(cursor).toBe(manual);
    });

    // Test Vector 2: Validation Success
    it("should validate a correct cursor", () => {
        const event: AuditEvent = {
            schema_version: "1",
            event_id: "evt_test",
            timestamp: 1234567890,
            cursor: deriveCursor(1234567890, "evt_test"),
            event_type: "SESSION",
            outcome: "OK",
            session_id: "s1",
            correlation_id: "c1",
            agent_id: "a1",
            peer_id: "p1",
            tool: "t1",
            method: "m1",
            hashes: {},
            integrity: {
                proof_state: "VERIFIED",
                signature_state: "VALID",
                anchor_state: "NOT_ENABLED",
                verifier_version: "1.0"
            },
            metadata: {}
        };

        const result = validateCursor(event);
        expect(result.ok).toBe(true);
        expect(result.derived).toBe(event.cursor);
    });

    // Test Vector 3: Cursor Mismatch
    it("should detect CURSOR_MISMATCH on tampered cursor", () => {
        const event: AuditEvent = {
            schema_version: "1",
            event_id: "evt_tampered",
            timestamp: 1234567890,
            cursor: "tampered_cursor_string",
            event_type: "SESSION",
            outcome: "OK",
            session_id: "s1",
            correlation_id: "c1",
            agent_id: "a1",
            peer_id: "p1",
            tool: "t1",
            method: "m1",
            hashes: {},
            integrity: {
                proof_state: "VERIFIED",
                signature_state: "VALID",
                anchor_state: "NOT_ENABLED",
                verifier_version: "1.0"
            },
            metadata: {}
        };

        const result = validateCursor(event);
        expect(result).toMatchObject({
            ok: false,
            reason: "CURSOR_MISMATCH"
        });
        expect(result.derived).not.toBe(event.cursor);
    });

    // Test Vector 4: Invalid Types (Frame Check)
    it("should detect INVALID_FRAME on bad types", () => {
        const event = {
            timestamp: "not-a-number", // Invalid
            event_id: 123, // Invalid
            cursor: null // Invalid
        } as unknown as AuditEvent;

        const result = validateCursor(event);
        expect(result).toMatchObject({
            ok: false,
            reason: "INVALID_FRAME"
        });
    });

    // Test Vector 5: Timestamp precision (Strict Integer Check)
    it("should reject floating point timestamps", () => {
        const tsFloat = 1700000000.999;
        const eventId = "evt_float";

        expect(() => deriveCursor(tsFloat, eventId)).toThrow("INVALID_FRAME");
    });
});
