"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { DashboardStats } from "@/lib/data/DataSource";
import { Activity, ShieldCheck, ShieldAlert, Zap } from "lucide-react";

interface KPIGridProps {
    stats: DashboardStats;
}

export function KPIGrid({ stats }: KPIGridProps) {
    const denialRate = stats.requests_24h > 0
        ? (1 - stats.auth_success_rate) * 100
        : 0;

    return (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <KPI
                label="Total Requests (24h)"
                value={stats.requests_24h.toLocaleString()}
                icon={<Activity className="text-zinc-400" />}
            />
            <KPI
                label="Auth Success Rate"
                value={`${(stats.auth_success_rate * 100).toFixed(1)}%`}
                icon={<ShieldCheck className="text-emerald-500" />}
                trend="+0.2%"
                trendUp={true}
            />
            <KPI
                label="Denial Rate"
                value={`${denialRate.toFixed(1)}%`}
                icon={<ShieldAlert className="text-amber-500" />}
            />
            <KPI
                label="Latency (p95)"
                value={stats.latency_percentiles ? `${stats.latency_percentiles.p95}ms` : "N/A"}
                icon={<Zap className="text-blue-500" />}
            />
        </div>
    );
}

function KPI({ label, value, icon, trend, trendUp }: {
    label: string;
    value: string;
    icon: React.ReactNode;
    trend?: string;
    trendUp?: boolean;
}) {
    return (
        <GlassPanel className="p-5 flex flex-col gap-1">
            <div className="flex items-center justify-between mb-2">
                <span className="text-zinc-500 text-xs uppercase tracking-wider font-semibold">{label}</span>
                {icon}
            </div>
            <div className="text-2xl font-bold font-mono text-zinc-100">{value}</div>
            {trend && (
                <div className={`text-xs ${trendUp ? 'text-emerald-500' : 'text-rose-500'} mt-1`}>
                    {trend} vs last 24h
                </div>
            )}
        </GlassPanel>
    );
}
