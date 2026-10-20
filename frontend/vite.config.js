import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        // Uploads run embedding generation synchronously; allow plenty of time
        // for the first request which may download the Sentence Transformers model.
        timeout: 600_000,
        proxyTimeout: 600_000,
      },
    },
  },
})
