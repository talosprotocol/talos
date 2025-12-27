import {
    AuditEvent,
    GatewayStatus,
    CursorPage,
    EvidenceBundle
} from "./schemas";
import { MOCK_EVENTS } from "./mock/events";
import { MOCK_GATEWAY_STATUS } from "./mock/status";

// --- Types ---

export type DataMode = "MOCK" | "SQLITE" | "HTTP" | "WS";

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

/**
 * Validate that an event's cursor matches the v3.2 spec derivation.
 * Per v3.2: cursor MUST equal base64url(utf8("{timestamp}:{event_id}"))
 * Returns true if valid, false if CURSOR_MISMATCH.
 */
export function validateCursor(event: { timestamp: number; event_id: string; cursor: string }): boolean {
    const expected = encodeCursor(event.timestamp, event.event_id);
    return event.cursor === expected;
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

class HttpDataSource implements DataSource {
    private baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    async getGatewayStatus(): Promise<GatewayStatus> {
        const res = await fetch(`${this.baseUrl}/api/gateway/status`);
        if (!res.ok) throw new Error("Failed to fetch status");
        return res.json();
    }

    async getStats(): Promise<DashboardStats> {
        // Fetch recent events to compute stats
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
        if (params.cursor) url.searchParams.set("cursor", params.cursor);

        const res = await fetch(url.toString());
        if (!res.ok) throw new Error("Failed to fetch events");
        return res.json();
    }

    subscribe(cb: (msg: StreamMessage) => void): () => void {
        // Polling fallback since WS is not yet implemented in Python server
        const interval = setInterval(async () => {
            try {
                // Poll status
                const status = await this.getGatewayStatus();
                cb({ type: "gateway_status", status });

                // Poll recent events (simplified)
                // In a real app we'd track last cursor

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
    mode === "HTTP" ? new HttpDataSource() :
        new MockDataSource();

if (mode !== "MOCK" && mode !== "HTTP") {
    console.warn(`Data Mode '${mode}' requested but not yet implemented. Falling back to MOCK.`);
}
