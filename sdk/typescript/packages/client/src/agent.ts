import { Capability, generateKeyPair, sign, fromSeed } from '@talos-protocol/sdk';

export interface KeyProvider {
    getPublicKey(): Promise<Uint8Array>;
    sign(data: Uint8Array): Promise<Uint8Array>;
}

export class InMemoryKeyProvider implements KeyProvider {
    private publicKey: Uint8Array;
    private privateKey: Uint8Array;

    constructor(seed?: Uint8Array) {
        if (seed) {
            const kp = fromSeed(seed);
            this.publicKey = kp.publicKey;
            this.privateKey = kp.privateKey;
        } else {
            const kp = generateKeyPair();
            this.publicKey = kp.publicKey;
            this.privateKey = kp.privateKey;
        }
    }

    async getPublicKey(): Promise<Uint8Array> {
        return this.publicKey;
    }

    async sign(data: Uint8Array): Promise<Uint8Array> {
        return sign(data, this.privateKey);
    }
}

export interface CapabilityStore {
    put(cap: Capability): Promise<void>;
    get(tool: string, method: string): Promise<Capability | undefined>;
}

export class InMemoryCapabilityStore implements CapabilityStore {
    private caps: Capability[] = [];

    async put(cap: Capability): Promise<void> {
        this.caps.push(cap);
    }

    async get(tool: string, _method: string): Promise<Capability | undefined> {
        // Simple lookup: find capability that covers scope.
        // In v1 we might just match scope string perfectly or assume "tool:name".
        // "scope = tool:<name>[/method:<name>]"
        // For now returning the most recent one for the tool?
        // Implementation Plan doesn't specify store logic deeply.
        // We'll just filter by exact scope match or prefix?
        // Let's assume exact match for tool scope or "tools/call" generic scope if user asks.
        return this.caps.find(c => c.scope.includes(tool));
    }
}

export class TalosAgent {
    constructor(
        public readonly agentId: string, // DID
        public readonly keyProvider: KeyProvider,
        public readonly capStore: CapabilityStore = new InMemoryCapabilityStore()
    ) { }
}
