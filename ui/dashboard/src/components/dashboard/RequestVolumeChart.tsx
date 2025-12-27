"use client";

import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { GlassPanel } from "@/components/ui/GlassPanel";

interface DataPoint {
    time: number;
    ok: number;
    deny: number;
    error: number;
}

interface RequestVolumeChartProps {
    data: DataPoint[];
}

function formatTime(timestamp: number): string {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}

function formatDate(timestamp: number): string {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function RequestVolumeChart({ data }: RequestVolumeChartProps) {
    if (!data || data.length === 0) {
        return (
            <GlassPanel className="p-4 h-64">
                <h3 className="text-sm font-medium text-[var(--text-muted)] mb-4">Request Volume (24h)</h3>
                <div className="flex items-center justify-center h-48 text-[var(--text-muted)] text-sm">
                    No data available
                </div>
            </GlassPanel>
        );
    }

    // Sort by time ascending for chart
    const sortedData = [...data].sort((a, b) => a.time - b.time);

    // Calculate totals for display
    const totals = sortedData.reduce(
        (acc, point) => ({
            ok: acc.ok + point.ok,
            deny: acc.deny + point.deny,
            error: acc.error + point.error,
        }),
        { ok: 0, deny: 0, error: 0 }
    );
    const grandTotal = totals.ok + totals.deny + totals.error;

    return (
        <GlassPanel className="p-4 h-64">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-[var(--text-muted)]">Request Volume (24h)</h3>
                <span className="text-xs text-[var(--text-muted)]">{grandTotal.toLocaleString()} total</span>
            </div>
            <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={sortedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                        <linearGradient id="gradientOk" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="gradientDeny" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="gradientError" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                            <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--glass-border)" opacity={0.3} />
                    <XAxis
                        dataKey="time"
                        tickFormatter={formatTime}
                        stroke="var(--text-muted)"
                        tick={{ fontSize: 10 }}
                        axisLine={{ stroke: "var(--glass-border)" }}
                        tickLine={{ stroke: "var(--glass-border)" }}
                    />
                    <YAxis
                        stroke="var(--text-muted)"
                        tick={{ fontSize: 10 }}
                        axisLine={{ stroke: "var(--glass-border)" }}
                        tickLine={{ stroke: "var(--glass-border)" }}
                    />
                    <Tooltip
                        contentStyle={{
                            backgroundColor: "var(--panel)",
                            border: "1px solid var(--glass-border)",
                            borderRadius: "8px",
                            boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
                        }}
                        labelStyle={{ color: "var(--text-primary)" }}
                        labelFormatter={(value) => `${formatDate(value)} ${formatTime(value)}`}
                        formatter={(value: number | undefined, name: string | undefined) => {
                            const label = name === "ok" ? "Success" : name === "deny" ? "Denied" : "Error";
                            return [value ?? 0, label];
                        }}
                    />
                    <Area
                        type="monotone"
                        dataKey="ok"
                        stackId="1"
                        stroke="#22c55e"
                        fill="url(#gradientOk)"
                        strokeWidth={2}
                    />
                    <Area
                        type="monotone"
                        dataKey="deny"
                        stackId="1"
                        stroke="#ef4444"
                        fill="url(#gradientDeny)"
                        strokeWidth={2}
                    />
                    <Area
                        type="monotone"
                        dataKey="error"
                        stackId="1"
                        stroke="#f97316"
                        fill="url(#gradientError)"
                        strokeWidth={2}
                    />
                </AreaChart>
            </ResponsiveContainer>
        </GlassPanel>
    );
}
