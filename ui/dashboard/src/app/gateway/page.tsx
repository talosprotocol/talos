"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { useDataSource } from "@/lib/hooks/useDataSource";
import { Server, Database, Activity } from "lucide-react";

export default function GatewayPage() {
    const { gatewayStatus, loading } = useDataSource();

    if (loading || !gatewayStatus) {
        return <div className="p-8 text-[var(--text-muted)]">Loading gateway status...</div>;
    }

    return (
        <main className="min-h-screen bg-[var(--bg)] p-8 font-sans text-[var(--text-primary)]">
            <header className="mb-8">
                <h1 className="text-2xl font-bold tracking-tight">Gateway Status</h1>
                <p className="text-[var(--text-muted)] text-sm">Infrastructure health and resource monitoring.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {/* Top Level Stats */}
                <StatusCard
                    label="State"
                    value={gatewayStatus.state}
                    icon={<Activity className={gatewayStatus.state === "RUNNING" ? "text-emerald-500" : "text-amber-500"} />}
                />
                <StatusCard
                    label="Version"
                    value={gatewayStatus.version}
                    icon={<Server className="text-[var(--text-muted)]" />}
                />
                <StatusCard
                    label="Uptime"
                    value={`${(gatewayStatus.uptime_seconds / 3600).toFixed(1)}h`}
                    icon={<ClockIcon />}
                />
                <StatusCard
                    label="Tenants"
                    value={gatewayStatus.tenants.toString()}
                    icon={<Database className="text-blue-500" />}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Cache Panel */}
                <GlassPanel className="p-6">
                    <h3 className="text-sm font-semibold text-[var(--text-secondary)] mb-6 flex items-center gap-2">
                        <Database className="w-4 h-4" /> Capability Cache
                    </h3>
                    <div className="grid grid-cols-2 gap-y-6 gap-x-12">
                        <StatRow label="Entries" value={gatewayStatus.cache.capability_cache_size} />
                        <StatRow label="Hits" value={gatewayStatus.cache.hits} highlight />
                        <StatRow label="Misses" value={gatewayStatus.cache.misses} />
                        <StatRow label="Evictions" value={gatewayStatus.cache.evictions} />
                    </div>
                </GlassPanel>

                {/* Sessions Panel */}
                <GlassPanel className="p-6">
                    <h3 className="text-sm font-semibold text-[var(--text-secondary)] mb-6 flex items-center gap-2">
                        <ShieldIcon /> Session Security
                    </h3>
                    <div className="space-y-6">
                        <div>
                            <div className="text-xs text-[var(--text-muted)] uppercase font-bold tracking-wider mb-1">Active Sessions</div>
                            <div className="text-3xl font-mono font-bold">{gatewayStatus.sessions.active_sessions}</div>
                        </div>
                        <div>
                            <div className="text-xs text-[var(--text-muted)] uppercase font-bold tracking-wider mb-1">Replay Rejections (1h)</div>
                            <div className="text-3xl font-mono font-bold text-rose-500">{gatewayStatus.sessions.replay_rejections_1h}</div>
                        </div>
                    </div>
                </GlassPanel>
            </div>

            <div className="mt-8">
                <GlassPanel className="p-4 text-xs font-mono text-[var(--text-muted)] flex justify-between">
                    <span>Status Sequence: {gatewayStatus.status_seq}</span>
                    <span>Schema v{gatewayStatus.schema_version}</span>
                </GlassPanel>
            </div>
        </main>
    );
}

function StatusCard({ label, value, icon }: { label: string, value: string, icon: React.ReactNode }) {
    return (
        <GlassPanel className="p-5 flex flex-col gap-1">
            <div className="flex items-center justify-between mb-2">
                <span className="text-[var(--text-muted)] text-xs uppercase tracking-wider font-semibold">{label}</span>
                {icon}
            </div>
            <div className="text-xl font-bold font-mono text-[var(--text-primary)]">{value}</div>
        </GlassPanel>
    )
}

function StatRow({ label, value, highlight }: { label: string, value: number, highlight?: boolean }) {
    return (
        <div>
            <div className="text-xs text-[var(--text-muted)] mb-1">{label}</div>
            <div className={`font-mono font-bold text-lg ${highlight ? "text-emerald-500" : "text-[var(--text-primary)]"}`}>
                {value.toLocaleString()}
            </div>
        </div>
    )
}

function ClockIcon() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--text-muted)] w-4 h-4"><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></svg>
    )
}

function ShieldIcon() {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
    )
}
