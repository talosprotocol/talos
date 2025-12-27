"use client";

import { useDataSource } from "@/lib/hooks/useDataSource";
import { GlassPanel } from "@/components/ui/GlassPanel";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { useMemo } from "react";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { computeSuspiciousScore } from "@/lib/analysis/scoring";

export default function SessionDetailPage({ params }: { params: { id: string } }) {
    const { events } = useDataSource();
    const sessionId = params.id;

    const sessionEvents = useMemo(() => {
        // Desc order by default in mock
        return events.filter(e => e.session_id === sessionId);
    }, [events, sessionId]);

    const scoreData = useMemo(() => {
        const scores = computeSuspiciousScore(sessionEvents);
        return scores.get(sessionId);
    }, [sessionEvents, sessionId]);

    // Note: hasMore=false for this MVP detail view as we rely on the main buffer.
    // Real implementation would fetch /sessions/:id/events stream.

    return (
        <main className="min-h-screen bg-[var(--bg)] p-8 font-sans text-zinc-100">
            <Link href="/sessions" className="flex items-center gap-2 mb-6 text-zinc-500 hover:text-zinc-300 text-sm w-fit">
                <ArrowLeft className="w-4 h-4" /> Back to Sessions
            </Link>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Stats & Meta */}
                <div className="space-y-6">
                    <GlassPanel className="p-6">
                        <div className="text-xs text-zinc-500 uppercase font-bold tracking-wider mb-1">Session ID</div>
                        <div className="text-lg font-mono font-bold break-all">{sessionId}</div>

                        <div className="mt-6 flex items-center justify-between">
                            <div className="text-xs text-zinc-500 uppercase font-bold tracking-wider">Risk Score</div>
                            <div className={`text-3xl font-mono font-bold ${scoreData && scoreData.score > 10 ? "text-rose-500" : "text-emerald-500"}`}>
                                {scoreData?.score ?? 0}
                            </div>
                        </div>
                    </GlassPanel>

                    <GlassPanel className="p-6">
                        <h3 className="text-sm font-semibold text-zinc-400 mb-4">Event Breakdown</h3>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-zinc-500">Total Events</span>
                                <span>{sessionEvents.length}</span>
                            </div>
                            <div className="flex justify-between text-rose-400">
                                <span>Replays</span>
                                <span>{scoreData?.breakdown.replays ?? 0}</span>
                            </div>
                            <div className="flex justify-between text-amber-400">
                                <span>Unknown Tools</span>
                                <span>{scoreData?.breakdown.unknownTools ?? 0}</span>
                            </div>
                        </div>
                    </GlassPanel>
                </div>

                {/* Right Column: Timeline */}
                <div className="lg:col-span-2">
                    <h2 className="text-lg font-bold mb-4">Session Timeline</h2>
                    <ActivityFeed
                        events={sessionEvents}
                        hasMore={false}
                        onLoadMore={() => { }}
                        isLoading={false}
                    />
                </div>
            </div>
        </main>
    );
}
