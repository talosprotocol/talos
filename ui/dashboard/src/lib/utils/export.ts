import { AuditEvent, EvidenceBundle, EvidenceBundleSchema } from "@/lib/data/schemas";

export function downloadEvidenceBundle(event: AuditEvent) {
    const bundle: EvidenceBundle = {
        evidence_bundle_version: "1",
        generated_at: new Date().toISOString(),
        redaction_mode: (process.env.NEXT_PUBLIC_TALOS_ALLOW_SAFE_METADATA === "true"
            ? "SAFE_METADATA"
            : "STRICT_HASH_ONLY"),
        events: [event],
        integrity_summary: {
            [event.outcome]: 1,
        }
    };

    // Validate against schema (optional runtime check)
    const valid = EvidenceBundleSchema.safeParse(bundle);
    if (!valid.success) {
        console.error("Bundle validation failed", valid.error);
        return;
    }

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
