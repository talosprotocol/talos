"use client";

import { dataSource, DashboardStats, StreamMessage } from "@/lib/data/DataSource";
import { AuditEvent, GatewayStatus } from "@/lib/data/schemas";
import { useEffect, useState, useCallback } from "react";

export function useDataSource() {
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [events, setEvents] = useState<AuditEvent[]>([]);
    const [gatewayStatus, setGatewayStatus] = useState<GatewayStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [cursor, setCursor] = useState<string | undefined>(undefined);
    const [hasMore, setHasMore] = useState(true);

    // Initial Load
    useEffect(() => {
        async function init() {
            try {
                const now = Math.floor(Date.now() / 1000);
                const [statsData, eventsPage, statusData] = await Promise.all([
                    dataSource.getStats({ from: now - 86400, to: now }),
                    dataSource.listAuditEvents({ limit: 20 }),
                    dataSource.getGatewayStatus()
                ]);

                setStats(statsData);
                setEvents(eventsPage.items);
                setCursor(eventsPage.next_cursor);
                setHasMore(eventsPage.has_more);
                setGatewayStatus(statusData);
            } catch (err) {
                console.error("Failed to load initial data", err);
            } finally {
                setLoading(false);
            }
        }
        init();

        // Subscribe to Live Stream
        const unsubscribe = dataSource.subscribe((msg: StreamMessage) => {
            if (msg.type === "audit_event") {
                setEvents(prev => {
                    // Dedupe global by event_id
                    if (prev.some(e => e.event_id === msg.event.event_id)) return prev;
                    return [msg.event, ...prev];
                });
                // Update stats logic (simplified)
                setStats(prev => {
                    if (!prev) return null;
                    return {
                        ...prev,
                        requests_24h: prev.requests_24h + 1,
                        // Note: Ideally we re-fetch stats occasionally
                    }
                })
            } else if (msg.type === "gateway_status") {
                setGatewayStatus(msg.status);
            }
        });

        return () => unsubscribe();
    }, []);

    const loadMore = useCallback(async () => {
        if (!cursor || loadingMore) return;
        setLoadingMore(true);
        try {
            const page = await dataSource.listAuditEvents({ limit: 20, cursor });
            setEvents(prev => [...prev, ...page.items]);
            setCursor(page.next_cursor);
            setHasMore(page.has_more);
        } catch (err) {
            console.error("Failed to load more events", err);
        } finally {
            setLoadingMore(false);
        }
    }, [cursor, loadingMore]);

    return {
        stats,
        events,
        gatewayStatus,
        loading,
        loadingMore,
        hasMore,
        loadMore
    };
}
