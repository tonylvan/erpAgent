import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# 便于 app.services 中 ontology 等 INFO 日志在控制台可见（与 uvicorn 并存时仅补充根 handler）
if not logging.root.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# 必须在 import app.* 之前执行：固定读取 backend/.env，避免从项目根目录启动 uvicorn 时读不到
_backend_root = Path(__file__).resolve().parent.parent
load_dotenv(_backend_root / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router

app = FastAPI(
    title="ERP Agent API",
    description="MetaERP 本体与智能编排服务",
    version="0.1.0",
)

origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
