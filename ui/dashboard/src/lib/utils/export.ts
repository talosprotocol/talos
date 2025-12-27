import { AuditEvent } from "@/lib/data/schemas";

/**
 * Sanitize an event for export by converting null to undefined for optional fields.
 * This ensures the event passes Zod validation in strict mode.
 */
function sanitizeEventForExport(event: AuditEvent): AuditEvent {
    return {
        ...event,
        denial_reason: event.denial_reason || undefined,
        metrics: event.metrics || undefined,
        hashes: {
            capability_hash: event.hashes.capability_hash || undefined,
            request_hash: event.hashes.request_hash || undefined,
            response_hash: event.hashes.response_hash || undefined,
            event_hash: event.hashes.event_hash || undefined,
        },
        integrity: {
            ...event.integrity,
            failure_reason: event.integrity.failure_reason || undefined,
            verified_at: event.integrity.verified_at || undefined,
        },
    };
}

export function downloadEvidenceBundle(event: AuditEvent) {
    // Sanitize the event to handle null vs undefined
    const sanitizedEvent = sanitizeEventForExport(event);

    const bundle = {
        evidence_bundle_version: "1" as const,
        generated_at: new Date().toISOString(),
        redaction_mode: (process.env.NEXT_PUBLIC_TALOS_ALLOW_SAFE_METADATA === "true"
            ? "SAFE_METADATA"
            : "STRICT_HASH_ONLY") as "STRICT_HASH_ONLY" | "SAFE_METADATA",
        events: [sanitizedEvent],
        integrity_summary: {
            [event.outcome]: 1,
        }
    };

    // Download without strict validation for now
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `evidence_${event.event_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
