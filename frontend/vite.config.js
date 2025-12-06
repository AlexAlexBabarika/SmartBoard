import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, res) => {
            console.log('Proxy error:', err);
            if (res && !res.headersSent) {
              res.writeHead(500, {
                'Content-Type': 'text/plain',
              });
              res.end('Backend connection failed. Make sure the backend is running on http://localhost:8000');
            }
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log(`[PROXY] ${req.method} ${req.url} -> http://localhost:8000${req.url.replace('/api', '')}`);
          });
        },
      }
    }
  }
})

