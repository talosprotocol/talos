"use client";

import { GlassPanel } from "@/components/ui/GlassPanel";
import { AuditEvent } from "@/lib/data/schemas";
import { CheckCircle, Shield, Hash, Copy, AlertTriangle, Download } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/cn";
import { downloadEvidenceBundle } from "@/lib/utils/export";

interface ProofDrawerProps {
    event: AuditEvent | null;
    onClose: () => void;
}

export function ProofDrawer({ event, onClose }: ProofDrawerProps) {
    if (!event) return null;

    return (
        <div className="fixed inset-y-0 right-0 w-[480px] bg-[var(--bg)] border-l border-[var(--glass-border)] shadow-2xl backdrop-blur-xl z-50 p-6 flex flex-col transform transition-transform duration-300">
            {/* Header */}
            <div className="flex items-start justify-between mb-8">
                <div>
                    <h2 className="text-xl font-bold text-[var(--text-primary)] flex items-center gap-2">
                        <Shield className="w-5 h-5 text-[var(--accent)]" />
                        Audit Proof
                    </h2>
                    <div className="text-xs text-[var(--text-muted)] font-mono mt-1">{event.event_id}</div>
                </div>
                <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]" aria-label="Close drawer">
                    ✕
                </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-6">
                {/* 1. Integrity State Machine */}
                <section>
                    <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] font-semibold mb-3">Integrity State</h3>
                    <div className="grid grid-cols-2 gap-3">
                        <StateCard
                            label="Proof State"
                            value={event.integrity.proof_state}
                            state={event.integrity.proof_state === "VERIFIED" ? "success" : event.integrity.proof_state === "FAILED" ? "danger" : "warning"}
                            icon={event.integrity.proof_state === "VERIFIED" ? CheckCircle : AlertTriangle}
                        />
                        <StateCard
                            label="Signature"
                            value={event.integrity.signature_state}
                            state={event.integrity.signature_state === "VALID" ? "success" : "danger"}
                        />
                    </div>

                    {event.integrity.failure_reason && (
                        <GlassPanel className="mt-3 p-3 bg-red-500/10 border-red-500/20 text-red-400 text-xs font-mono">
                            FAILURE_REASON: {event.integrity.failure_reason}
                        </GlassPanel>
                    )}
                </section>

                {/* 2. Bindings & Hashes */}
                <section>
                    <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] font-semibold mb-3">Cryptographic Bindings</h3>
                    <div className="space-y-2">
                        <HashRow label="Event Hash" value={event.hashes.event_hash} required />
                        <HashRow label="Capability Hash" value={event.hashes.capability_hash} />
                        <HashRow label="Request Hash" value={event.hashes.request_hash} />
                        <HashRow label="Response Hash" value={event.hashes.response_hash} />
                    </div>
                </section>

                {/* 3. Session Context */}
                <section>
                    <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] font-semibold mb-3">Session Context</h3>
                    <GlassPanel className="p-4 space-y-3">
                        <ContextRow label="Session ID" value={event.session_id} />
                        <ContextRow label="Correlation ID" value={event.correlation_id} />
                        <ContextRow label="Peer ID" value={event.peer_id} />
                        <ContextRow label="Tool / Method" value={`${event.tool || "N/A"} : ${event.method || "N/A"} `} />
                    </GlassPanel>
                </section>

                {/* 4. Anchor State */}
                <section>
                    <h3 className="text-xs uppercase tracking-wider text-[var(--text-muted)] font-semibold mb-3">Blockchain Anchor</h3>
                    <div className="flex items-center gap-3 p-3 rounded-lg border border-[var(--glass-border)] bg-[var(--panel)]">
                        <div className={cn(
                            "w-2 h-2 rounded-full",
                            event.integrity.anchor_state === "ANCHORED" ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-[var(--glass-border)]"
                        )} />
                        <div className="flex-1">
                            <div className="text-sm font-medium text-[var(--text-primary)]">{event.integrity.anchor_state}</div>
                            <div className="text-xs text-[var(--text-muted)]">Verifier: {event.integrity.verifier_version}</div>
                        </div>
                    </div>
                </section>
            </div>

            {/* Footer */}
            <div className="pt-6 mt-6 border-t border-[var(--glass-border)]">
                <GlassPanel
                    variant="hoverable"
                    className="flex items-center justify-center p-3 gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors cursor-pointer"
                    onClick={() => downloadEvidenceBundle(event)}
                >
                    <Download className="w-4 h-4" />
                    <span className="text-sm font-medium">Export Evidence JSON</span>
                </GlassPanel>
            </div>
        </div>
    );
}

function StateCard({ label, value, state, icon: Icon }: { label: string, value: string, state: "success" | "warning" | "danger", icon?: React.ElementType }) {
    const colors = {
        success: "text-emerald-400 bg-emerald-500/5 border-emerald-500/20",
        warning: "text-amber-400 bg-amber-500/5 border-amber-500/20",
        danger: "text-rose-400 bg-rose-500/5 border-rose-500/20"
    };

    return (
        <GlassPanel className={cn("p-3 flex flex-col gap-1", colors[state])}>
            <div className="text-[10px] uppercase font-bold opacity-70 flex items-center gap-1">
                {Icon && <Icon className="w-3 h-3" />}
                {label}
            </div>
            <div className="font-mono text-sm font-semibold truncate">{value}</div>
        </GlassPanel>
    )
}

function HashRow({ label, value, required }: { label: string, value?: string, required?: boolean }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        if (value) {
            navigator.clipboard.writeText(value);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="group flex items-center justify-between p-2 rounded hover:bg-white/5 transition-colors">
            <div className="flex items-center gap-2 overflow-hidden">
                <Hash className={cn("w-3 h-3", value ? "text-[var(--accent)]" : "text-[var(--text-muted)]")} />
                <div className="flex flex-col min-w-0">
                    <span className="text-xs text-[var(--text-muted)] font-medium">{label}</span>
                    <span className={cn("text-xs font-mono truncate", value ? "text-[var(--text-primary)]" : "text-[var(--text-muted)] italic")}>
                        {value || (required ? "MISSING" : "Not Present")}
                    </span>
                </div>
            </div>
            {value && (
                <button onClick={handleCopy} className="p-1.5 rounded hover:bg-white/10 text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors" aria-label="Copy hash">
                    {copied ? <CheckCircle className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
            )}
        </div>
    )
}

function ContextRow({ label, value }: { label: string, value: string }) {
    return (
        <div className="flex flex-col gap-0.5">
            <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">{label}</span>
            <span className="text-sm font-mono text-[var(--text-primary)] truncate select-all">{value}</span>
        </div>
    )
}
