import { defineConfig, createLogger } from 'vite'
import react from '@vitejs/plugin-react'

const logger = createLogger()
const originalInfo = logger.info

logger.info = (msg, options) => {
  // Filter out HMR update logs to keep console clean
  if (msg.includes('hmr update')) return
  originalInfo(msg, options)
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  customLogger: logger,
  clearScreen: false,
  server: {
    host: true, // Listen on all local IPs
    port: 5173,
    allowedHosts: 'all', // 允許所有主機連線（內網開發用）
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/outputs': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      }
    }
  },
})
