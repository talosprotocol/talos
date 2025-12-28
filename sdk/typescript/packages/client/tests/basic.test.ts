import { describe, it, expect } from 'vitest';
import { TalosAgent } from '../src/index';

describe('TalosAgent', () => {
    it('should be exported', () => {
        expect(TalosAgent).toBeDefined();
    });
});
