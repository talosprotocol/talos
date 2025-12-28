"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { computeSuspiciousScore } from "@/lib/analysis/scoring";
import { useDataSource } from "@/lib/hooks/useDataSource";
import { AlertTriangle, Clock, ShieldAlert } from "lucide-react";
import { useMemo } from "react";
import Link from "next/link";

export default function SessionsPage() {
    const { events, loading } = useDataSource();

    const sessionScores = useMemo(() => {
        const scoresMap = computeSuspiciousScore(events);
        return Array.from(scoresMap.values()).sort((a, b) => b.score - a.score || b.lastActive - a.lastActive);
    }, [events]);

    if (loading && sessionScores.length === 0) {
        return <div className="p-8 text-[var(--text-muted)]">Loading sessions...</div>;
    }

    return (
        <main className="min-h-screen bg-[var(--bg)] p-8 font-sans text-[var(--text-primary)]">
            <header className="mb-8">
                <h1 className="text-2xl font-bold tracking-tight">Active Sessions</h1>
                <p className="text-[var(--text-muted)] text-sm">Real-time threat analysis and suspicious activity scoring.</p>
            </header>

            <div className="grid grid-cols-1 gap-4">
                {sessionScores.map(session => (
                    <Link key={session.sessionId} href={`/sessions/${session.sessionId}`}>
                        <GlassPanel variant="hoverable" className="p-4 flex items-center justify-between group cursor-pointer">
                            <div className="flex items-center gap-4">
                                <div className="flex flex-col">
                                    <div className="text-sm font-mono font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors">
                                        {session.sessionId}
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                                        <Clock className="w-3 h-3" />
                                        Last Active: {new Date(session.lastActive * 1000).toLocaleTimeString()}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-8">
                                {/* Breakdown */}
                                <div className="flex gap-4 text-xs text-[var(--text-muted)]">
                                    {session.breakdown.replays > 0 && (
                                        <span className="flex items-center gap-1 text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded">
                                            <ShieldAlert className="w-3 h-3" />
                                            {session.breakdown.replays} Replays
                                        </span>
                                    )}
                                    {session.breakdown.unknownTools > 0 && (
                                        <span className="flex items-center gap-1 text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">
                                            <AlertTriangle className="w-3 h-3" />
                                            {session.breakdown.unknownTools} Unknown Tools
                                        </span>
                                    )}
                                </div>

                                {/* Score */}
                                <div className="text-right">
                                    <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold tracking-wider">Risk Score</div>
                                    <div className={`text-2xl font-mono font-bold ${session.score > 10 ? "text-rose-500" : session.score > 0 ? "text-amber-500" : "text-emerald-500"}`}>
                                        {session.score}
                                    </div>
                                </div>
                            </div>
                        </GlassPanel>
                    </Link>
                ))}

                {sessionScores.length === 0 && (
                    <div className="text-center py-10 text-[var(--text-muted)]">No active sessions found.</div>
                )}
            </div>
        </main>
    )
}
