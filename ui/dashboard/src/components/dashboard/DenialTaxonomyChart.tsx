"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { GlassPanel } from "@/components/ui/GlassPanel";

interface DenialTaxonomyChartProps {
    data: Record<string, number>;
}

// Color palette for denial reasons
const COLORS: Record<string, string> = {
    NO_CAPABILITY: "#ef4444",      // red
    EXPIRED: "#f97316",            // orange  
    REVOKED: "#eab308",            // yellow
    SCOPE_MISMATCH: "#22c55e",     // green
    DELEGATION_INVALID: "#06b6d4", // cyan
    UNKNOWN_TOOL: "#3b82f6",       // blue
    REPLAY: "#8b5cf6",             // purple
    SIGNATURE_INVALID: "#ec4899",  // pink
    INVALID_FRAME: "#6366f1",      // indigo
};

const DEFAULT_COLOR = "#64748b"; // slate

// Human-readable labels
const LABELS: Record<string, string> = {
    NO_CAPABILITY: "No Capability",
    EXPIRED: "Expired",
    REVOKED: "Revoked",
    SCOPE_MISMATCH: "Scope Mismatch",
    DELEGATION_INVALID: "Invalid Delegation",
    UNKNOWN_TOOL: "Unknown Tool",
    REPLAY: "Replay Attack",
    SIGNATURE_INVALID: "Invalid Signature",
    INVALID_FRAME: "Invalid Frame",
};

export function DenialTaxonomyChart({ data }: DenialTaxonomyChartProps) {
    const chartData = Object.entries(data)
        .filter(([, count]) => count > 0)
        .map(([reason, count]) => ({
            name: LABELS[reason] || reason,
            value: count,
            reason,
        }))
        .sort((a, b) => b.value - a.value);

    const total = chartData.reduce((sum, item) => sum + item.value, 0);

    if (total === 0) {
        return (
            <GlassPanel className="p-4 h-64">
                <h3 className="text-sm font-medium text-[var(--text-muted)] mb-4">Denial Taxonomy</h3>
                <div className="flex items-center justify-center h-48 text-[var(--text-muted)] text-sm">
                    No denials recorded
                </div>
            </GlassPanel>
        );
    }

    return (
        <GlassPanel className="p-4 h-64">
            <h3 className="text-sm font-medium text-[var(--text-muted)] mb-2">Denial Taxonomy</h3>
            <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                    <Pie
                        data={chartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={70}
                        paddingAngle={2}
                        dataKey="value"
                        stroke="none"
                    >
                        {chartData.map((entry) => (
                            <Cell
                                key={entry.reason}
                                fill={COLORS[entry.reason] || DEFAULT_COLOR}
                                className="transition-opacity hover:opacity-80"
                            />
                        ))}
                    </Pie>
                    <Tooltip
                        contentStyle={{
                            backgroundColor: "var(--panel)",
                            border: "1px solid var(--glass-border)",
                            borderRadius: "8px",
                            boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
                        }}
                        labelStyle={{ color: "var(--text-primary)" }}
                        itemStyle={{ color: "var(--text-secondary)" }}
                        formatter={(value: number | undefined, name: string | undefined) => [
                            `${value ?? 0} (${(((value ?? 0) / total) * 100).toFixed(1)}%)`,
                            name ?? "",
                        ]}
                    />
                    <Legend
                        layout="vertical"
                        align="right"
                        verticalAlign="middle"
                        wrapperStyle={{ fontSize: "11px", color: "var(--text-muted)" }}
                        formatter={(value) => (
                            <span style={{ color: "var(--text-secondary)" }}>{value}</span>
                        )}
                    />
                </PieChart>
            </ResponsiveContainer>
        </GlassPanel>
    );
}
