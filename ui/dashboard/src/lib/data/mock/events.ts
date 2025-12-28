import { AuditEvent } from "../schemas";
import { deriveCursor } from "../../integrity/cursor";

// Helper to generate deterministic events
const BASE_TIME = 1700000000; // Fixed timestamp base

const RAW_EVENTS: AuditEvent[] = [
    // --- SESSION A: Good Behavior ---
    {
        schema_version: "1",
        event_id: "evt_001",
        timestamp: BASE_TIME - 3600,
        cursor: "", // Placeholder
        event_type: "SESSION",
        outcome: "OK",
        session_id: "sess_alpha",
        correlation_id: "corr_a1",
        agent_id: "agent_alpha",
        peer_id: "peer_good",
        tool: "system",
        method: "connect",
        hashes: { event_hash: "hash_evt_001" },
        integrity: {
            proof_state: "VERIFIED",
            signature_state: "VALID",
            anchor_state: "ANCHORED",
            verifier_version: "1.0.0",
        },
        metadata: { msg: "Session established" },
    },
    {
        schema_version: "1",
        event_id: "evt_002",
        timestamp: BASE_TIME - 3500,
        cursor: "",
        event_type: "AUTHORIZATION",
        outcome: "OK",
        session_id: "sess_alpha",
        correlation_id: "corr_a2",
        agent_id: "agent_alpha",
        peer_id: "peer_good",
        tool: "files",
        method: "read",
        hashes: {
            capability_hash: "hash_cap_read",
            request_hash: "hash_req_002",
            event_hash: "hash_evt_002",
        },
        integrity: {
            proof_state: "VERIFIED",
            signature_state: "VALID",
            anchor_state: "ANCHORED",
            verifier_version: "1.0.0",
        },
        metadata: { path: "/etc/hosts" },
    },

    // --- SESSION B: Suspicious Replay Attack ---
    {
        schema_version: "1",
        event_id: "evt_003",
        timestamp: BASE_TIME - 1800,
        cursor: "",
        event_type: "AUTHORIZATION",
        outcome: "OK",
        session_id: "sess_beta",
        correlation_id: "corr_b1",
        agent_id: "agent_beta",
        peer_id: "peer_attacker",
        tool: "payments",
        method: "transfer",
        hashes: {
            capability_hash: "hash_cap_pay",
            request_hash: "hash_req_003",
            event_hash: "hash_evt_003",
        },
        integrity: {
            proof_state: "VERIFIED",
            signature_state: "VALID",
            anchor_state: "PENDING",
            verifier_version: "1.0.0",
        },
        metadata: { amount: 1000 },
    },
    {
        schema_version: "1",
        event_id: "evt_004", // REPLAY ATTEMPT
        timestamp: BASE_TIME - 1799,
        cursor: "",
        event_type: "DENIAL",
        outcome: "DENY",
        denial_reason: "REPLAY",
        session_id: "sess_beta",
        correlation_id: "corr_b1", // Same correlation ID
        agent_id: "agent_beta",
        peer_id: "peer_attacker",
        tool: "payments",
        method: "transfer",
        hashes: {
            capability_hash: "hash_cap_pay",
            request_hash: "hash_req_003", // Same request hash
            event_hash: "hash_evt_004",
        },
        integrity: {
            proof_state: "VERIFIED", // Sig is valid, but logic denied it
            signature_state: "VALID",
            anchor_state: "NOT_ENABLED",
            verifier_version: "1.0.0",
        },
        metadata: { risk_score: 0.99 },
    },

    // --- SESSION C: Tools Not Allowed ---
    {
        schema_version: "1",
        event_id: "evt_005",
        timestamp: BASE_TIME - 600,
        cursor: "",
        event_type: "DENIAL",
        outcome: "DENY",
        denial_reason: "UNKNOWN_TOOL",
        session_id: "sess_gamma",
        correlation_id: "corr_c1",
        agent_id: "agent_gamma",
        peer_id: "peer_lost",
        tool: "admin_shell",
        method: "exec",
        hashes: {
            request_hash: "hash_req_005",
            event_hash: "hash_evt_005",
        },
        integrity: {
            proof_state: "FAILED", // No capability, maybe no sig
            signature_state: "NOT_PRESENT",
            anchor_state: "NOT_ENABLED",
            verifier_version: "1.0.0",
            failure_reason: "MISSING_INPUTS",
        },
        metadata: {},
    },

    // --- BURST TRAFFIC (OK) ---
    ...Array.from({ length: 20 }, (_, i) => ({
        schema_version: "1" as const,
        event_id: `evt_burst_${i}`,
        timestamp: BASE_TIME - 60 + i,
        cursor: "",
        event_type: "AUTHORIZATION" as const,
        outcome: "OK" as const,
        session_id: "sess_delta",
        correlation_id: `corr_d${i}`,
        agent_id: "agent_delta",
        peer_id: "peer_bot",
        tool: "logger",
        method: "log",
        hashes: { event_hash: `hash_burst_${i}` },
        integrity: {
            proof_state: "VERIFIED" as const,
            signature_state: "VALID" as const,
            anchor_state: "PENDING" as const,
            verifier_version: "1.0.0",
        },
        metadata: { index: i },
    })),

    // --- Invalid Signature ---
    {
        schema_version: "1",
        event_id: "evt_026",
        timestamp: BASE_TIME - 10,
        cursor: "",
        event_type: "DENIAL",
        outcome: "DENY",
        denial_reason: "SIGNATURE_INVALID",
        session_id: "sess_epsilon",
        correlation_id: "corr_e1",
        agent_id: "agent_epsilon",
        peer_id: "peer_fuzzer",
        tool: "auth",
        method: "login",
        hashes: { event_hash: "hash_evt_026" },
        integrity: {
            proof_state: "FAILED",
            signature_state: "INVALID",
            anchor_state: "NOT_ENABLED",
            verifier_version: "1.0.0",
            failure_reason: "SIGNATURE_INVALID",
        },
        metadata: {},
    }
];

// Calculate derived cursors for all except the one we corrupted manually
export const MOCK_EVENTS = RAW_EVENTS.map(evt => {
    if (evt.cursor && evt.cursor !== "") return evt; // Keep manual overrides
    return {
        ...evt,
        cursor: deriveCursor(evt.timestamp, evt.event_id)
    };
});
