import { z } from "zod";

// --- Enums & Literals ---

export const DenialReasonSchema = z.enum([
    "NO_CAPABILITY",
    "EXPIRED",
    "REVOKED",
    "SCOPE_MISMATCH",
    "DELEGATION_INVALID",
    "UNKNOWN_TOOL",
    "REPLAY",
    "SIGNATURE_INVALID",
    "INVALID_FRAME",
]);

export const ProofStateSchema = z.enum([
    "VERIFIED",
    "UNVERIFIED",
    "FAILED",
    "MISSING_INPUTS",
]);

export const AnchorStateSchema = z.enum([
    "NOT_ENABLED",
    "PENDING",
    "ANCHORED",
    "ANCHOR_FAILED",
]);

export const SignatureStateSchema = z.enum(["VALID", "INVALID", "NOT_PRESENT"]);

export const EventTypeSchema = z.enum([
    "AUTHORIZATION",
    "DENIAL",
    "REVOCATION",
    "SESSION",
    "ERROR",
]);

export const OutcomeSchema = z.enum(["OK", "DENY", "ERROR"]);

// --- Audit Event Schema ---

export const RedactionPolicySchema = z.enum([
    "STRICT_HASH_ONLY",
    "SAFE_METADATA",
    "FULL_DEBUG",
]);

export const AuditEventSchema = z.object({
    schema_version: z.literal("1"),
    event_id: z.string(),
    timestamp: z.number().int(), // Unix seconds
    cursor: z.string(), // Opaque Base64URL
    event_type: EventTypeSchema,
    outcome: OutcomeSchema,
    denial_reason: DenialReasonSchema.optional(),

    session_id: z.string().min(1),
    correlation_id: z.string().default(""),
    agent_id: z.string().default(""), // Added agent_id
    peer_id: z.string().default(""),
    tool: z.string().default(""),
    method: z.string().default(""),

    metrics: z.object({
        latency_ms: z.number().optional(),
    }).optional(),

    hashes: z.object({
        capability_hash: z.string().optional(),
        request_hash: z.string().optional(),
        response_hash: z.string().optional(),
        event_hash: z.string().optional(),
    }),

    integrity: z.object({
        proof_state: ProofStateSchema,
        signature_state: SignatureStateSchema,
        anchor_state: AnchorStateSchema,
        verifier_version: z.string(),
        verified_at: z.number().optional(),
        failure_reason: z
            .enum([
                "MISSING_INPUTS",
                "MISSING_EVENT_HASH",
                "MISSING_SIGNATURE",
                "SIGNATURE_INVALID",
                "ANCHOR_PENDING",
                "ANCHOR_FAILED",
                "VERIFIER_ERROR",
                "UNSUPPORTED_SCHEMA_VERSION",
                "CURSOR_MISMATCH",
            ])
            .optional(),
    }),

    metadata: z.record(z.string(), z.unknown()).default({}),
})
    .refine((data) => {
        // Integrity Constraint: If outcome is DENY, denial_reason MUST be present
        if (data.outcome === "DENY" && !data.denial_reason) {
            return false;
        }
        // Integrity Constraint: If outcome is OK, denial_reason MUST be absent
        if (data.outcome === "OK" && data.denial_reason) {
            return false;
        }
        return true;
    }, {
        message: "Invalid denial_reason state for outcome",
        path: ["denial_reason"],
    });

export type AuditEvent = z.infer<typeof AuditEventSchema>;

// --- Gateway Status Schema ---

export const GatewayStatusSchema = z.object({
    schema_version: z.literal("1"),
    gateway_instance_id: z.string().optional(), // v3.2: Unique per process
    status_seq: z.number().int(),
    state: z.enum(["STARTING", "RUNNING", "DEGRADED", "STOPPED"]),
    version: z.string(),
    uptime_seconds: z.number(),
    requests_processed: z.number(),
    tenants: z.number(),

    cache: z.object({
        capability_cache_size: z.number(),
        hits: z.number(),
        misses: z.number(),
        evictions: z.number(),
    }),

    sessions: z.object({
        active_sessions: z.number(),
        replay_rejections_1h: z.number(),
    }),
});

export type GatewayStatus = z.infer<typeof GatewayStatusSchema>;

// --- Cursor Page ---

export interface CursorPage<T> {
    items: T[];
    next_cursor?: string;
    has_more: boolean;
}

// --- Verification & Evidence ---

export const EvidenceBundleSchema = z.object({
    evidence_bundle_version: z.literal("1"),
    generated_at: z.string(), // ISO String
    redaction_mode: RedactionPolicySchema,
    filters: z.record(z.string(), z.string()).optional(),
    cursor_range: z.object({
        start_cursor: z.string().optional(),
        end_cursor: z.string().optional(),
    }).optional(),
    gateway_snapshot: GatewayStatusSchema.optional(),
    events: z.array(AuditEventSchema),
    integrity_summary: z.record(z.string(), z.number()), // Breakdown counts
});

export type EvidenceBundle = z.infer<typeof EvidenceBundleSchema>;
