import { AuditEvent } from "@/lib/data/schemas";

export interface SessionScore {
    sessionId: string;
    score: number;
    breakdown: {
        replays: number;
        unknownTools: number;
        invalidSigs: number;
        denials: number;
    };
    lastActive: number;
}

export function computeSuspiciousScore(events: AuditEvent[]): Map<string, SessionScore> {
    const scores = new Map<string, SessionScore>();

    for (const event of events) {
        if (!event.session_id) continue;

        if (!scores.has(event.session_id)) {
            scores.set(event.session_id, {
                sessionId: event.session_id,
                score: 0,
                breakdown: { replays: 0, unknownTools: 0, invalidSigs: 0, denials: 0 },
                lastActive: 0
            });
        }

        const entry = scores.get(event.session_id)!;

        // Update Last Active
        if (event.timestamp > entry.lastActive) {
            entry.lastActive = event.timestamp;
        }

        // Apply Scoring Rules
        if (event.denial_reason === "REPLAY") {
            entry.score += 5;
            entry.breakdown.replays++;
        }
        if (event.denial_reason === "UNKNOWN_TOOL") {
            entry.score += 3;
            entry.breakdown.unknownTools++;
        }
        if (event.denial_reason === "SIGNATURE_INVALID" || event.denial_reason === "INVALID_FRAME") {
            entry.score += 2;
            entry.breakdown.invalidSigs++;
        }
        if (event.outcome === "DENY") {
            entry.score += 1;
            entry.breakdown.denials++;
        }
    }

    return scores;
}
