"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { AlertTriangle, Database, Lock, Radio, FlaskConical, ShieldAlert, RotateCw } from "lucide-react";
import { getIntegrityStatus, getBackfillStatus, IntegrityStatus, BackfillStatus } from "@/lib/data/DataSource";
import { useEffect, useState } from "react";

export function StatusBanners() {
    const mode = process.env.NEXT_PUBLIC_TALOS_DATA_MODE || "HTTP";
    const allowSafeMetadata = process.env.NEXT_PUBLIC_TALOS_ALLOW_SAFE_METADATA === "true";

    // Client-side polling for global state
    // In a real app, this would use React Context or a reactive store
    const [integrity, setIntegrity] = useState<IntegrityStatus>("OK");
    const [backfill, setBackfill] = useState<BackfillStatus>("IDLE");

    useEffect(() => {
        const interval = setInterval(() => {
            setIntegrity(getIntegrityStatus());
            setBackfill(getBackfillStatus());
        }, 1000); // Check status every second
        return () => clearInterval(interval);
    }, []);

    // Determine if we're in demo/test mode
    const isDemo = mode === "MOCK" || mode === "HTTP"; // LIVE mode disables this badge

    return (
        <div className="flex items-center gap-3 text-xs font-mono flex-wrap">
            {/* --- CRITICAL INTEGRITY BANNER --- */}
            {integrity === "CURSOR_MISMATCH" && (
                <GlassPanel className="px-3 py-1.5 flex items-center gap-2 text-white bg-red-600 border-red-500 animate-pulse font-bold shadow-lg shadow-red-900/50">
                    <ShieldAlert className="w-4 h-4" />
                    <span>INTEGRITY FAILURE: Cursor mismatch detected. Event log may be tampered.</span>
                </GlassPanel>
            )}

            {/* Backfill Status */}
            {backfill === "ACTIVE" && (
                <GlassPanel className="px-3 py-1.5 flex items-center gap-2 text-cyan-400 bg-cyan-500/10 border-cyan-500/30">
                    <RotateCw className="w-3 h-3 animate-spin" />
                    <span>Backfilling history...</span>
                </GlassPanel>
            )}

            {(backfill === "PARTIAL" || backfill === "FAILED") && (
                <GlassPanel className="px-3 py-1.5 flex items-center gap-2 text-amber-400 bg-amber-500/10 border-amber-500/30">
                    <AlertTriangle className="w-3 h-3" />
                    <span>History Gap: Partial Data</span>
                </GlassPanel>
            )}

            {/* Data Mode Pill */}
            <GlassPanel className={`px-3 py-1.5 flex items-center gap-2 ${mode === "WS" || mode === "LIVE"
                ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                : mode === "HTTP"
                    ? "text-blue-400 bg-blue-500/10 border-blue-500/30"
                    : "text-amber-400 bg-amber-500/10 border-amber-500/30"
                }`}>
                {mode === "WS" ? (
                    <Radio className="w-3 h-3 animate-pulse" />
                ) : mode === "MOCK" ? (
                    <FlaskConical className="w-3 h-3" />
                ) : (
                    <Database className="w-3 h-3" />
                )}
                <span>
                    {mode === "MOCK" ? "MOCK DATA" : (mode === "HTTP" || mode === "LIVE") ? "LIVE TRAFFIC" : "STREAMING"}
                </span>
            </GlassPanel>

            {/* Demo Banner - shown when using generated traffic */}
            {isDemo && (
                <GlassPanel className="px-3 py-1.5 flex items-center gap-2 text-purple-400 bg-purple-500/10 border-purple-500/30">
                    <FlaskConical className="w-3 h-3" />
                    <span>DEMO TRAFFIC</span>
                </GlassPanel>
            )}

            {/* Redaction Policy */}
            <GlassPanel className="px-3 py-1.5 flex items-center gap-2 text-[var(--text-muted)] bg-[var(--glass-border)]/50">
                <Lock className="w-3 h-3" />
                <span>REDACTION: {allowSafeMetadata ? "SAFE_METADATA" : "STRICT_HASH_ONLY"}</span>
            </GlassPanel>

            {allowSafeMetadata && (
                <GlassPanel className="px-3 py-1.5 flex items-center gap-2 text-amber-500 bg-amber-500/10 border-amber-500/20">
                    <AlertTriangle className="w-3 h-3" />
                    <span>NON-PROD METADATA</span>
                </GlassPanel>
            )}
        </div>
    );
}
