import { GatewayStatus } from "../schemas";

export const MOCK_GATEWAY_STATUS: GatewayStatus = {
    schema_version: "1",
    status_seq: 105,
    state: "RUNNING",
    version: "3.0.0-rc1",
    uptime_seconds: 48500,
    requests_processed: 1250394,
    tenants: 12,
    cache: {
        capability_cache_size: 4500,
        hits: 1240000,
        misses: 10394,
        evictions: 50,
    },
    sessions: {
        active_sessions: 142,
        replay_rejections_1h: 24, // Matches the suspicious events
    },
};
