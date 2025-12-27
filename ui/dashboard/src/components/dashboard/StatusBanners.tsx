"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { AlertTriangle, Database, Lock, Radio } from "lucide-react";

export function StatusBanners() {
    const mode = process.env.NEXT_PUBLIC_TALOS_DATA_MODE || "MOCK";
    const allowSafeMetadata = process.env.NEXT_PUBLIC_TALOS_ALLOW_SAFE_METADATA === "true";

    return (
        <div className="flex items-center gap-3 text-xs font-mono mb-6 flex-wrap">
            <GlassPanel className="px-3 py-1.5 flex items-center gap-2 text-blue-400 bg-blue-500/5 border-blue-500/20">
                {mode === "WS" ? <Radio className="w-3 h-3 animate-pulse" /> : <Database className="w-3 h-3" />}
                <span>MODE: {mode}</span>
            </GlassPanel>

            <GlassPanel className="px-3 py-1.5 flex items-center gap-2 text-[var(--text-muted)] bg-[var(--glass-border)]/50">
                <Lock className="w-3 h-3" />
                <span>REDACTION: {allowSafeMetadata ? "SAFE_METADATA" : "STRICT_HASH_ONLY"}</span>
            </GlassPanel>

            {allowSafeMetadata && (
                <GlassPanel className="px-3 py-1.5 flex items-center gap-2 text-amber-500 bg-amber-500/10 border-amber-500/20">
                    <AlertTriangle className="w-3 h-3" />
                    <span>NON-PROD METADATA ENABLED</span>
                </GlassPanel>
            )}
        </div>
    );
}
