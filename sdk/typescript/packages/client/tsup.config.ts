import { defineConfig } from 'tsup';

export default defineConfig({
    entry: {
        node: 'src/index.ts', // Entry for Node, handles exports differently if strictly needed, but let's assume index is enough
        browser: 'src/index.ts',
    },
    format: ['esm'],
    dts: true,
    clean: true,
    splitting: false, // For single file outputs
});
