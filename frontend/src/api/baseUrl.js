/**
 * 开发时可在 `frontend/.env.development` 设置 VITE_API_BASE（如 http://127.0.0.1:8001）
 * 直连 FastAPI，避免仅依赖 Vite 代理时端口不一致导致 /api 404。
 * 未设置时走相对路径（由 Vite proxy 转发）。
 */
export function apiUrl(path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  const raw = import.meta.env.VITE_API_BASE;
  if (raw != null && String(raw).trim() !== "") {
    const base = String(raw).trim().replace(/\/$/, "");
    return `${base}${p}`;
  }
  return p;
}
