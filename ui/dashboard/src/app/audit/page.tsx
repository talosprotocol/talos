"use client";

import { useState, useCallback, useEffect } from "react";
import { useDataSource } from "@/lib/hooks/useDataSource";
import { AuditTable } from "@/components/dashboard/AuditTable";
import { dataSource } from "@/lib/data/DataSource";
import { AuditEvent, CursorPage } from "@/lib/data/schemas";
import { ListFilter } from "lucide-react";
import { GlassPanel } from "@/components/ui/GlassPanel";

export default function AuditPage() {
    // We use a custom fetch implementation here for virtualization support
    // The global useDataSource hook is optimized for the Overview stream
    const [data, setData] = useState<AuditEvent[]>([]);
    const [cursor, setCursor] = useState<string | undefined>(undefined);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);

    const fetchMore = useCallback(async () => {
        if (loading || !hasMore) return;
        setLoading(true);
        try {
            const page = await dataSource.listAuditEvents({
                limit: 50,
                cursor: cursor
            });

            setData(prev => {
                // Simple append for now, but virtualizer handles rendering
                // For true 50k rows, we normally just keep appending to memory. 
                // 50k objects in memory is approx 50MB, manageable for desktop browser.
                return [...prev, ...page.items];
            });

            setCursor(page.next_cursor);
            setHasMore(page.has_more);
        } catch (err) {
            console.error("Audit load error", err);
        } finally {
            setLoading(false);
        }
    }, [cursor, loading, hasMore]);

    // Initial Load
    useEffect(() => {
        fetchMore();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <main className="h-screen bg-[var(--bg)] flex flex-col font-sans text-zinc-100 overflow-hidden">
            <header className="flex-shrink-0 h-16 border-b border-[var(--glass-border)] bg-zinc-900/50 backdrop-blur px-6 flex items-center justify-between">
                <h1 className="font-bold text-lg tracking-tight">Audit Explorer</h1>

                <div className="flex items-center gap-2">
                    <GlassPanel variant="hoverable" className="px-3 py-1.5 flex items-center gap-2 text-xs text-zinc-400">
                        <ListFilter className="w-3.5 h-3.5" />
                        <span>Filters</span>
                    </GlassPanel>
                </div>
            </header>

            <div className="flex-1 p-6 overflow-hidden">
                <AuditTable
                    data={data}
                    total={data.length}
                    onFetchMore={fetchMore}
                    isLoading={loading}
                />
            </div>
        </main>
    );
}
