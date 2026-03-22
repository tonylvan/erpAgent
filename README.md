# ERP Agent

FastAPI 后端 + Vue 3（Vite）前端骨架。

## 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # 必填：在 .env 中设置 NEO4J_PASSWORD（Neo4j 密码）
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

默认前端将 `/api` 代理到 **http://127.0.0.1:8001**（与上述端口一致，避免与本机占用 **8000** 的其他应用冲突）。若后端改用其他端口，请设置 **`VITE_PROXY_API`** 或修改 `frontend/vite.config.js` 里的 `API_TARGET`，并同步 **`frontend/.env.development`** 中的 **`VITE_API_BASE`**。

- 健康检查: <http://127.0.0.1:8001/health>
- API 文档: <http://127.0.0.1:8001/docs>
- 本体全景（Neo4j）: `GET /api/graph/ontology` — 同上；若 **Database does not exist**，执行 `SHOW DATABASES` 后设置 **`NEO4J_DATABASE`**；若 **Unauthorized / authentication failure**，核对 **`NEO4J_USER` / `NEO4J_PASSWORD`** 与 Neo4j 登录一致。若**图谱无数据**，看响应 `meta` 中的 **`neo4j_total_nodes` / `hint`**（常见：连错库、库为空、`NEO4J_IGNORE_LABELS` 过滤掉全部标签）

## 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 <http://localhost:5173>。开发时默认在 `frontend/.env.development` 中配置了 **`VITE_API_BASE=http://127.0.0.1:8001`**，前端会直连 FastAPI；若后端端口不同请改该变量或删除后改用代理。

前端主界面：左侧为 P2P 时序图谱画布（占位），右侧为本体对象 / 预测规划与事件回放 / 结果呈现（演示数据，待接 API）。

## 目录

- `backend/app/main.py` — FastAPI 入口、CORS、`/api` 路由
- `frontend/` — Vue 3 + Vite
- `frontend/src/components/` — 画布与各面板组件
