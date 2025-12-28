"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { AuditEvent } from "@/lib/data/schemas";
import { cn } from "@/lib/cn";
import { AlertCircle, ArrowRightLeft, CheckCircle, ShieldAlert, Terminal } from "lucide-react";
import { useState } from "react";
import { ProofDrawer, computeProofBadge } from "./ProofDrawer";

interface ActivityFeedProps {
    events: AuditEvent[];
    hasMore: boolean;
    onLoadMore: () => void;
    isLoading: boolean;
}

export function ActivityFeed({ events, hasMore, onLoadMore, isLoading }: ActivityFeedProps) {
    const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);

    return (
        <>
            <div className="w-full space-y-2">
                <h3 className="text-sm font-semibold text-[var(--text-muted)] mb-4 px-1">Live Activity Stream</h3>

                {events.length === 0 && !isLoading && (
                    <div className="text-center py-10 text-[var(--text-muted)] text-sm">No activity recorded</div>
                )}

                <div className="space-y-2 pb-4">
                    {events.map((event) => (
                        <ActivityItem
                            key={`${event.timestamp}-${event.event_id}`} // Dedupe key requirement
                            event={event}
                            onClick={() => setSelectedEvent(event)}
                        />
                    ))}
                </div>

                {hasMore && (
                    <button
                        onClick={onLoadMore}
                        disabled={isLoading}
                        className="w-full py-3 text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] bg-[var(--panel)] hover:bg-[var(--panel-hover)] border border-[var(--glass-border)] rounded-lg transition-colors"
                    >
                        {isLoading ? "Loading..." : "Load Older Events"}
                    </button>
                )}
            </div>

            {/* Drawer Overlay */}
            {selectedEvent && (
                <>
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity" onClick={() => setSelectedEvent(null)} />
                    <ProofDrawer event={selectedEvent} onClose={() => setSelectedEvent(null)} />
                </>
            )}
        </>
    );
}

function ActivityItem({ event, onClick }: { event: AuditEvent, onClick: () => void }) {
    const isError = event.outcome === "ERROR";
    const isDeny = event.outcome === "DENY";

    return (
        <GlassPanel
            variant="hoverable"
            onClick={onClick}
            className="flex items-center gap-4 p-3 group"
        >
            {/* Icon Status */}
            <div className={cn(
                "p-2 rounded-lg flex-shrink-0",
                isError ? "bg-red-500/10 text-red-500" :
                    isDeny ? "bg-amber-500/10 text-amber-500" :
                        "bg-emerald-500/10 text-emerald-500"
            )}>
                {isError ? <AlertCircle className="w-4 h-4" /> :
                    isDeny ? <ShieldAlert className="w-4 h-4" /> :
                        <CheckCircle className="w-4 h-4" />}
            </div>

            {/* Main Content */}
            <div className="flex-1 min-w-0 grid grid-cols-1 md:grid-cols-12 gap-2 md:gap-4 items-start md:items-center">

                {/* Time & Method */}
                <div className="col-span-1 md:col-span-4 flex items-center justify-between md:justify-start gap-2 w-full">
                    <div className="flex items-center gap-2">
                        <span className="text-[var(--text-primary)] font-semibold text-sm truncate">{event.method}</span>
                        <span className="px-1.5 py-0.5 text-[10px] uppercase font-mono bg-[var(--glass-border)] text-[var(--text-secondary)] rounded">{event.event_type}</span>
                    </div>
                    {/* Time visible on right for mobile, inline for desktop */}
                    <div className="text-xs text-[var(--text-muted)] font-mono md:hidden">
                        {new Date(event.timestamp * 1000).toLocaleTimeString()}
                    </div>
                </div>

                {/* Desktop Timestamp (Hidden on mobile to avoid dupe) */}
                <div className="hidden md:block md:col-span-4 text-xs text-[var(--text-muted)] font-mono">
                    {new Date(event.timestamp * 1000).toLocaleTimeString()}
                </div>

                {/* Identity & Hash - Stacked on mobile */}
                <div className="col-span-1 md:col-span-4 flex items-center justify-between md:justify-end gap-2 w-full">
                    {/* Identity */}
                    <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                        <Terminal className="w-3 h-3" />
                        <span className="truncate max-w-[120px]" title={event.peer_id || event.agent_id}>
                            {event.peer_id ? `Peer: ${event.peer_id.slice(0, 8)}...` : `Agent: ${event.agent_id.slice(0, 8)}...`}
                        </span>
                    </div>

                    {/* Integrity Indicators */}
                    {(() => {
                        const badge = computeProofBadge(event.integrity);
                        const isMismatch = event.integrity.failure_reason === "CURSOR_MISMATCH";

                        // Critical Mismatch
                        if (isMismatch) {
                            return (
                                <div className="flex items-center gap-1 text-[10px] font-bold text-red-500 bg-red-500/10 px-1.5 py-0.5 rounded animate-pulse">
                                    <ShieldAlert className="w-3 h-3" />
                                    <span>TAMPERED</span>
                                </div>
                            )
                        }

                        // Other Failures
                        if (badge === "FAILED") {
                            return (
                                <div className="flex items-center gap-1 text-[10px] font-bold text-red-500 bg-red-500/10 px-1.5 py-0.5 rounded">
                                    <ShieldAlert className="w-3 h-3" />
                                    <span>FAILED</span>
                                </div>
                            )
                        }

                        // Missing/Unverified (Optional: only show if relevant, maybe generic shield?)
                        if (badge === "MISSING_INPUTS") {
                            return (
                                <span title="Missing Inputs">
                                    <AlertCircle className="w-3 h-3 text-amber-500" />
                                </span>
                            )
                        }

                        return null;
                    })()}

                    {/* Denial Reason / Hash */}
                    <div className="text-right">
                        {isDeny ? (
                            <span className="px-2 py-1 bg-amber-500/10 text-amber-500 text-[10px] font-bold rounded uppercase">
                                {event.denial_reason}
                            </span>
                        ) : (
                            <div className="flex items-center justify-end gap-1 text-[10px] text-[var(--text-muted)] font-mono">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/50 animate-pulse" />
                                {event.hashes.request_hash?.slice(0, 8)}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            <ArrowRightLeft className="w-4 h-4 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] transition-colors" />
        </GlassPanel>
    )
}
