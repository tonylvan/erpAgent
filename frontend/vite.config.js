import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

/** 与 `uvicorn ... --port` 一致（使用 8005 端口） */
const API_TARGET = process.env.VITE_PROXY_API ?? "http://127.0.0.1:8005";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true, // 允许局域网访问 (明确启用)
    port: 5180,
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
      },
      "/health": {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
  /** `npm run preview` 也会走代理，否则 /api 会 404 */
  preview: {
    port: 4173,
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
      },
      "/health": {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
