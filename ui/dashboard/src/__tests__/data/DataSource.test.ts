import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { HttpDataSource } from "../../lib/data/DataSource";
import { AuditEvent, CursorPage, GatewayStatus } from "../../lib/data/schemas";

// Mock fetch globally
const fetchMock = vi.fn();
global.fetch = fetchMock;

describe("HttpDataSource Backfill (v3.2)", () => {
    let ds: HttpDataSource;

    beforeEach(() => {
        vi.useFakeTimers();
        ds = new HttpDataSource();
        fetchMock.mockReset();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it("should poll for status and events, then trigger backfill execution", async () => {
        // --- Setup Mocks ---

        // 1. Mock Status Response
        const mockStatus: GatewayStatus = {
            schema_version: "1",
            gateway_instance_id: "gw_test",
            status_seq: 1,
            state: "RUNNING",
            uptime_seconds: 100,
            requests_processed: 1000,
            tenants: 1,
            version: "3.2.0",
            cache: {
                capability_cache_size: 10,
                hits: 10,
                misses: 2,
                evictions: 0
            },
            sessions: {
                active_sessions: 5,
                replay_rejections_1h: 0
            }
        };

        // 2. Mock Recent Events (Live Poll)
        // Assume we get 1 event initially
        const recentEvent: AuditEvent = {
            schema_version: "1",
            event_id: "evt_live_1",
            timestamp: 1000,
            cursor: "cursor_1000",
            event_type: "SESSION", // Valid enum value
            outcome: "OK",         // Valid enum value
            session_id: "s1",
            correlation_id: "c1",
            agent_id: "a1",
            peer_id: "p1",
            tool: "t1",
            method: "m1",
            hashes: {},
            integrity: { proof_state: "VERIFIED", signature_state: "VALID", anchor_state: "NOT_ENABLED", verifier_version: "1", failure_reason: "CURSOR_MISMATCH" },
            metadata: {}
        };
        const recentPage: CursorPage<AuditEvent> = {
            items: [recentEvent],
            next_cursor: "cursor_1000",
            has_more: true
        };

        // 3. Mock Backfill Page 1
        const backfillEvent1: AuditEvent = {
            ...recentEvent,
            event_id: "evt_old_1",
            timestamp: 900,
            cursor: "cursor_900"
        };
        // Remove mismatch for this one to vary tests? Or keep it to see log? 
        // Let's keep it consistent.

        const backfillPage1: CursorPage<AuditEvent> = {
            items: [backfillEvent1],
            next_cursor: "cursor_900",
            has_more: true
        };

        // 4. Mock Backfill Page 2 (Empty/Genesis)
        const backfillPage2: CursorPage<AuditEvent> = {
            items: [],
            has_more: false
        };

        // --- Mock Implementation ---

        fetchMock.mockImplementation((url: string) => {
            if (url.includes("/status")) {
                return Promise.resolve({
                    ok: true,
                    json: () => Promise.resolve(mockStatus)
                });
            }
            if (url.includes("/events")) {
                const u = new URL(url);
                const before = u.searchParams.get("before");

                // If no 'before' (limit=10), it's the live poll
                if (!before || u.searchParams.get("limit") === "10") {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve(recentPage)
                    });
                }

                // If 'before' is what we saw last time (cursor_1000), return older page
                if (before === "cursor_1000") {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve(backfillPage1)
                    });
                }

                // If 'before' is cursor_900, return empty (genesis)
                if (before === "cursor_900") {
                    return Promise.resolve({
                        ok: true,
                        json: () => Promise.resolve(backfillPage2)
                    });
                }
            }
            return Promise.reject(new Error("Unknown URL: " + url));
        });

        // --- Execution ---

        const callback = vi.fn();
        const unsubscribe = ds.subscribe(callback);

        // Advance timer to trigger first poll (Wait 2000ms)
        await vi.advanceTimersByTimeAsync(2000);

        // EXPECTATIONS:
        // 1. Status callback
        expect(callback).toHaveBeenCalledWith({ type: "gateway_status", status: mockStatus });

        // 2. Event callback (Live)
        expect(callback).toHaveBeenCalledWith({ type: "audit_event", event: recentEvent });

        // Let's verify backfill happened:
        expect(callback).toHaveBeenCalledWith({ type: "audit_event", event: backfillEvent1 });

        // Now next tick (another 2000ms), it should try to fetch from cursor_900
        await vi.advanceTimersByTimeAsync(2000);

        expect(fetchMock).toHaveBeenCalledTimes(6); // 2 status, 2 live, 2 backfill? 

        unsubscribe();
    });
});
