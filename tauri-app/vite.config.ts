import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const host = process.env.TAURI_DEV_HOST;

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  define: {
    // API base URL, can be overridden via VITE_API_BASE env var
    'import.meta.env.VITE_API_BASE': JSON.stringify(
      process.env.VITE_API_BASE || 'http://localhost:8000'
    ),
  },
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1421,
        }
      : undefined,
    watch: {
      ignored: ["**/src-tauri/**"],
    },
  },
});
