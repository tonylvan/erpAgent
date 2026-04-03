import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

/** 与 `uvicorn ... --port` 一致（默认 8001，避免与本机其他占用 8000 的服务冲突） */
const API_TARGET = process.env.VITE_PROXY_API ?? "http://127.0.0.1:8001";

export default defineConfig({
  plugins: [vue()],
  server: {
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
});
