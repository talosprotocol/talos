import {
    AuditEvent,
    GatewayStatus,
    CursorPage,
    EvidenceBundle
} from "./schemas";
import { MOCK_EVENTS } from "./mock/events";
import { MOCK_GATEWAY_STATUS } from "./mock/status";

// --- Types ---

export type DataMode = "MOCK" | "SQLITE" | "HTTP" | "WS" | "LIVE";
export interface DashboardStats {
    requests_24h: number;
    auth_success_rate: number;
    denial_reason_counts: Record<string, number>;
    request_volume_series: { time: number; ok: number; deny: number; error: number }[];
    latency_percentiles?: { p50: number; p95: number; p99: number };
}

export interface AuditFilters {
    correlation_id?: string;
    session_id?: string;
    outcome?: "OK" | "DENY" | "ERROR";
    denial_reason?: string;
    from?: number;
    to?: number;
}

export type StreamMessage =
    | { type: "audit_event"; event: AuditEvent }
    | { type: "gateway_status"; status: GatewayStatus }
    | { type: "cursor_gap"; from: string; to: string };

export interface DataSource {
    getStats(range: { from: number; to: number }): Promise<DashboardStats>;
    listAuditEvents(params: {
        limit: number;
        cursor?: string;
        filters?: AuditFilters
    }): Promise<CursorPage<AuditEvent>>;
    getGatewayStatus(): Promise<GatewayStatus>;
    subscribe(cb: (msg: StreamMessage) => void): () => void;
    exportEvidence?(params: { cursor_range?: { start?: string; end?: string }, filters?: AuditFilters }): Promise<EvidenceBundle>;
}

// --- Cursor Utils ---

import { validateCursor } from "../integrity/cursor";

// --- Cursor Utils ---

function encodeCursor(timestamp: number, eventId: string): string {
    const raw = `${timestamp}:${eventId}`;
    if (typeof window !== "undefined") {
        return window.btoa(raw).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    }
    return Buffer.from(raw).toString("base64url");
}

function decodeCursor(cursor: string): { timestamp: number; eventId: string } | null {
    try {
        let raw: string;
        if (typeof window !== "undefined") {
            // Re-add padding might be needed for strict atob, but usually fine
            raw = window.atob(cursor.replace(/-/g, '+').replace(/_/g, '/'));
        } else {
            raw = Buffer.from(cursor, "base64url").toString();
        }

        const parts = raw.split(":");
        if (parts.length !== 2) return null;
        return { timestamp: parseInt(parts[0], 10), eventId: parts[1] };
    } catch {
        return null;
    }
}

// --- v3.2 Cursor Comparators (Frozen) ---

type CursorKey = { timestamp: number; eventId: string };

/**
 * Extract cursor key from an event.
 * Per v3.2: cursor_key(event) = (event.timestamp, event.event_id)
 */
export function cursorKey(event: { timestamp: number; event_id: string }): CursorKey {
    return { timestamp: event.timestamp, eventId: event.event_id };
}

/**
 * Compare cursor keys for ordering.
 * Per v3.2: older_or_equal(a, b) = a.timestamp < b.timestamp OR 
 *           (a.timestamp == b.timestamp AND a.event_id <= b.event_id)
 */
export function olderOrEqual(a: CursorKey, b: CursorKey): boolean {
    if (a.timestamp < b.timestamp) return true;
    if (a.timestamp === b.timestamp && a.eventId <= b.eventId) return true;
    return false;
}

// --- Mock Implementation ---

class MockDataSource implements DataSource {
    private events = [...MOCK_EVENTS].sort((a, b) => b.timestamp - a.timestamp); // DESC

    async getGatewayStatus(): Promise<GatewayStatus> {
        return MOCK_GATEWAY_STATUS;
    }

    async getStats(range: { from: number; to: number }): Promise<DashboardStats> {
        const inRange = this.events.filter(e => e.timestamp >= range.from && e.timestamp <= range.to);

        // Compute Counts
        const total = inRange.length;
        const ok = inRange.filter(e => e.outcome === "OK").length;

        const denial_counts: Record<string, number> = {};
        inRange.filter(e => e.outcome === "DENY").forEach(e => {
            const reason = e.denial_reason || "UNKNOWN";
            denial_counts[reason] = (denial_counts[reason] || 0) + 1;
        });

        // Mock Series (Hourly buckets)
        const seriesMap = new Map<number, { ok: number, deny: number, error: number }>();
        inRange.forEach(e => {
            const bucket = Math.floor(e.timestamp / 3600) * 3600;
            if (!seriesMap.has(bucket)) seriesMap.set(bucket, { ok: 0, deny: 0, error: 0 });
            const entry = seriesMap.get(bucket)!;
            if (e.outcome === "OK") entry.ok++;
            else if (e.outcome === "DENY") entry.deny++;
            else entry.error++;
        });

        return {
            requests_24h: total,
            auth_success_rate: total > 0 ? ok / total : 1,
            denial_reason_counts: denial_counts,
            request_volume_series: Array.from(seriesMap.entries())
                .map(([time, data]) => ({ time, ...data }))
                .sort((a, b) => a.time - b.time),
            latency_percentiles: { p50: 5, p95: 12, p99: 45 }, // Mocked
        };
    }

    async listAuditEvents({ limit, cursor, filters }: {
        limit: number;
        cursor?: string;
        filters?: AuditFilters
    }): Promise<CursorPage<AuditEvent>> {
        let subset = this.events;

        // Apply Filters
        if (filters) {
            if (filters.outcome) subset = subset.filter(e => e.outcome === filters.outcome);
            if (filters.session_id) subset = subset.filter(e => e.session_id === filters.session_id);
            if (filters.correlation_id) subset = subset.filter(e => e.correlation_id === filters.correlation_id);
            if (filters.denial_reason) subset = subset.filter(e => e.denial_reason === filters.denial_reason);
        }

        // Apply Cursor (Pagination)
        if (cursor) {
            const decoded = decodeCursor(cursor);
            if (decoded) {
                // Find split point: Older than timestamp (DESC)
                // Or same timestamp but smaller ID
                subset = subset.filter(e => {
                    if (e.timestamp < decoded.timestamp) return true;
                    if (e.timestamp === decoded.timestamp && e.event_id < decoded.eventId) return true;
                    return false;
                });
            }
        }

        const items = subset.slice(0, limit);
        const lastItem = items[items.length - 1];

        return {
            items,
            next_cursor: lastItem ? encodeCursor(lastItem.timestamp, lastItem.event_id) : undefined,
            has_more: subset.length > limit,
        };
    }

    subscribe(cb: (msg: StreamMessage) => void): () => void {
        // Mock live stream: emit a random event every 5 seconds
        const interval = setInterval(() => {
            const randomEvent = this.events[Math.floor(Math.random() * this.events.length)];
            // Clone and bump timestamp to make it "new"
            const newEvent: AuditEvent = {
                ...randomEvent,
                event_id: `evt_live_${Date.now()}`,
                timestamp: Math.floor(Date.now() / 1000),
                cursor: encodeCursor(Math.floor(Date.now() / 1000), `evt_live_${Date.now()}`)
            };
            cb({ type: "audit_event", event: newEvent });
        }, 5000);
        return () => clearInterval(interval);
    }
}

// --- HTTP Implementation ---

// --- Integrity & Backfill State ---

export type IntegrityStatus = "OK" | "CURSOR_MISMATCH" | "INVALID_FRAME";
export type BackfillStatus = "IDLE" | "ACTIVE" | "COMPLETE" | "PARTIAL" | "FAILED";

// Private global state (since DataSource is singleton-ish)
let _integrityStatus: IntegrityStatus = "OK";
let _backfillStatus: BackfillStatus = "IDLE";
let _backfillLoadedCount = 0;

export function getIntegrityStatus() { return _integrityStatus; }
export function getBackfillStatus() { return _backfillStatus; }

// --- HTTP Implementation ---

// Safety caps for backfill
const BACKFILL_MAX_EVENTS = 1000;
const BACKFILL_PAGE_SIZE = 100;

export class HttpDataSource implements DataSource {
    private baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    async getGatewayStatus(): Promise<GatewayStatus> {
        const res = await fetch(`${this.baseUrl}/api/gateway/status`);
        if (!res.ok) throw new Error("Failed to fetch status");
        return res.json();
    }

    async getStats(): Promise<DashboardStats> {
        // Fetch recent events to compute stats (peek)
        const res = await this.listAuditEvents({ limit: 500 });
        const events = res.items;

        // Compute counts
        const total = events.length;
        const ok = events.filter(e => e.outcome === "OK").length;

        // Compute denial reason counts
        const denial_counts: Record<string, number> = {};
        events.filter(e => e.outcome === "DENY").forEach(e => {
            const reason = e.denial_reason || "UNKNOWN";
            denial_counts[reason] = (denial_counts[reason] || 0) + 1;
        });

        // Compute hourly series
        const seriesMap = new Map<number, { ok: number; deny: number; error: number }>();
        events.forEach(e => {
            const bucket = Math.floor(e.timestamp / 3600) * 3600;
            if (!seriesMap.has(bucket)) seriesMap.set(bucket, { ok: 0, deny: 0, error: 0 });
            const entry = seriesMap.get(bucket)!;
            if (e.outcome === "OK") entry.ok++;
            else if (e.outcome === "DENY") entry.deny++;
            else entry.error++;
        });

        return {
            requests_24h: total,
            auth_success_rate: total > 0 ? ok / total : 1,
            denial_reason_counts: denial_counts,
            request_volume_series: Array.from(seriesMap.entries())
                .map(([time, data]) => ({ time, ...data }))
                .sort((a, b) => a.time - b.time),
            latency_percentiles: { p50: 10, p95: 20, p99: 50 },
        };
    }

    async listAuditEvents(params: {
        limit: number;
        cursor?: string;
        filters?: AuditFilters
    }): Promise<CursorPage<AuditEvent>> {
        const url = new URL(`${this.baseUrl}/api/events`);
        url.searchParams.set("limit", params.limit.toString());
        // v3.2 Spec: GET /api/events?before={cursor}
        if (params.cursor) url.searchParams.set("before", params.cursor);

        const res = await fetch(url.toString());
        if (!res.ok) throw new Error("Failed to fetch events");

        const data: CursorPage<AuditEvent> = await res.json();

        // --- ENFORCEMENT: Validate Cursors on Ingress ---
        data.items.forEach(event => this.ingestEvent(event));

        return data;
    }

    private ingestEvent(event: AuditEvent) {
        const validation = validateCursor(event);
        if (!validation.ok) {
            console.error("Integrity Failure:", {
                eventId: event.event_id,
                received: event.cursor,
                derived: validation.derived,
                reason: validation.reason
            });

            // 1. Set global status for the critical banner
            if (validation.reason) {
                _integrityStatus = validation.reason;
            }

            // 2. Flag the event (per-row badge UI)
            // We mutate the event object before it goes to the UI
            if (!event.integrity) {
                event.integrity = {
                    proof_state: "FAILED",
                    signature_state: "INVALID",
                    anchor_state: "NOT_ENABLED",
                    verifier_version: "3.2"
                };
            }
            if (validation.reason === "CURSOR_MISMATCH") {
                event.integrity.failure_reason = "CURSOR_MISMATCH";
            }
        }
    }

    subscribe(cb: (msg: StreamMessage) => void): () => void {
        // Polling loop (v1: HttpDataSource)
        // Includes Automatic Backfill Logic
        let oldestLoadedCursor: string | undefined = undefined;

        const interval = setInterval(async () => {
            try {
                // 1. Poll Status
                const status = await this.getGatewayStatus();
                cb({ type: "gateway_status", status });

                // 2. Poll Recent Events (Live update)
                const recent = await this.listAuditEvents({ limit: 10 });
                if (recent.items.length > 0) {
                    recent.items.forEach(e => cb({ type: "audit_event", event: e }));

                    // Helper: Track oldest cursor seen this session for backfill anchor
                    if (!oldestLoadedCursor && recent.items.length > 0) {
                        oldestLoadedCursor = recent.items[recent.items.length - 1].cursor;
                    }
                }

                // 3. Backfill Loop (v3.2 Spec: "Gap in history detection")
                if (_backfillStatus === "IDLE" && oldestLoadedCursor && _backfillLoadedCount < BACKFILL_MAX_EVENTS) {
                    _backfillStatus = "ACTIVE";

                    console.log(`Backfilling from cursor: ${oldestLoadedCursor}`);
                    const page = await this.listAuditEvents({
                        limit: BACKFILL_PAGE_SIZE,
                        cursor: oldestLoadedCursor // passed as 'before' param
                    });

                    if (page.items.length === 0) {
                        _backfillStatus = "COMPLETE"; // Genesis reached
                    } else {
                        page.items.forEach(e => cb({ type: "audit_event", event: e }));
                        _backfillLoadedCount += page.items.length;

                        const newOldest = page.items[page.items.length - 1].cursor;

                        if (newOldest === oldestLoadedCursor || !page.next_cursor) {
                            // Loop trigger protection or end of stream
                            // If no next_cursor, we are done
                            if (!page.next_cursor) {
                                _backfillStatus = "COMPLETE";
                            } else {
                                _backfillStatus = "FAILED";
                                console.warn("Backfill stuck: cursor did not verify progress.");
                            }
                        } else {
                            oldestLoadedCursor = newOldest;
                            if (_backfillLoadedCount >= BACKFILL_MAX_EVENTS) {
                                _backfillStatus = "PARTIAL"; // Safety cap hit
                            } else {
                                _backfillStatus = "IDLE"; // Continue next tick
                            }
                        }
                    }
                }

            } catch (e) {
                console.error("Polling error", e);
            }
        }, 2000);
        return () => clearInterval(interval);
    }
}

// --- Factory ---

const mode = (process.env.NEXT_PUBLIC_TALOS_DATA_MODE || "MOCK") as DataMode;

export const dataSource: DataSource =
    (mode === "HTTP" || mode === "LIVE") ? new HttpDataSource() :
        new MockDataSource();

if (mode !== "MOCK" && mode !== "HTTP" && mode !== "LIVE") {
    console.warn(`Data Mode '${mode}' requested but not yet implemented. Falling back to MOCK.`);
}
