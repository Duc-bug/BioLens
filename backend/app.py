"""
BioLens - FastAPI Application Entrypoint
Khởi tạo ứng dụng FastAPI phục vụ mô hình BioCLIP 2, xử lý ngoại lệ tập trung và giao diện tĩnh.
"""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.exceptions import BioLensBaseError
from backend.routes import router as api_router
from configs.settings import PROJECT_ROOT

logger = logging.getLogger("biolens")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

FRONTEND_DIR = PROJECT_ROOT / "frontend"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Đang khởi động hệ thống BioLens Vietnam (BioCLIP 2)...")

    try:
        from models.inference_engine import BioLensInferenceEngine
        engine = BioLensInferenceEngine()
        logger.info(f"BioLensInferenceEngine đã nạp thành công trên thiết bị: {engine.device}")
    except Exception as exc:
        logger.warning(f"Khởi tạo BioLensInferenceEngine: {exc}")

    yield

    logger.info("Đang dừng BioLens Web Application...")


app = FastAPI(
    title="BioLens — Hệ thống Nhận diện Thực vật & Nấm Dược liệu Việt Nam",
    description="Ứng dụng nhận diện 3.570 loài thực vật và nấm dược liệu Việt Nam dựa trên BioCLIP 2",
    version="2.0.0",
    lifespan=lifespan,
)

# Cấu hình CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Global Exception Handlers (Kỹ thuật 6: Quản lý Ngoại lệ tập trung)
# ==============================================================================

@app.exception_handler(BioLensBaseError)
async def biolens_exception_handler(request: Request, exc: BioLensBaseError) -> JSONResponse:
    """Bắt và chuẩn hóa toàn bộ các lỗi thuộc cây phả hệ BioLensBaseError."""
    logger.error(f"[BioLens Error] {exc.error_code} - {exc.message} (Path: {request.url.path})")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


# Đăng ký Router
app.include_router(api_router)

# Mount thư mục Frontend tĩnh
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def serve_index() -> FileResponse:
    """Trang chủ giao diện Web BioLens."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return JSONResponse({"message": "BioLens Backend is running."})


@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon() -> Response:
    """Trả về biểu tượng favicon cho trình duyệt."""
    svg_icon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🌿</text></svg>'
    return Response(content=svg_icon, media_type="image/svg+xml")
