"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { AlertTriangle, Database, Lock, Radio, FlaskConical } from "lucide-react";

export function StatusBanners() {
    const mode = process.env.NEXT_PUBLIC_TALOS_DATA_MODE || "HTTP";
    const allowSafeMetadata = process.env.NEXT_PUBLIC_TALOS_ALLOW_SAFE_METADATA === "true";

    // Determine if we're in demo/test mode
    const isDemo = mode === "MOCK" || mode === "HTTP"; // HTTP with demo traffic gen is still demo

    return (
        <div className="flex items-center gap-3 text-xs font-mono flex-wrap">
            {/* Data Mode Pill */}
            <GlassPanel className={`px-3 py-1.5 flex items-center gap-2 ${mode === "WS"
                    ? "text-green-400 bg-green-500/10 border-green-500/30"
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
                    {mode === "MOCK" ? "MOCK DATA" : mode === "HTTP" ? "LIVE API" : "STREAMING"}
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
