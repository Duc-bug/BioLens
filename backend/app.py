from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from configs.settings import PROJECT_ROOT
from backend.routes import router as api_router

FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(
    title="BioLens — Hệ thống Nhận diện Sinh vật & Thực vật Dược liệu Việt Nam",
    description="Đồ án môn Học máy và Ứng dụng trên bộ dữ liệu VietMediSpecies2026 (3,570 loài / 310,647 ảnh)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def serve_index():
    """Trang chủ giao diện Web BioLens."""
    return FileResponse(FRONTEND_DIR / "index.html")
