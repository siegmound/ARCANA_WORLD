import { defineConfig } from 'vite';

export default defineConfig({
  base: '/',
  esbuild: { jsx: 'automatic' },
  // The Windows workspace sandbox permits reads but rejects native realpath on F:.
  resolve: { preserveSymlinks: true },
  define: { CESIUM_BASE_URL: JSON.stringify('/cesium/') },
  server: { host: '127.0.0.1', port: 5173, strictPort: true },
  preview: { host: '127.0.0.1', port: 4173, strictPort: true },
});
