"""
Cac route API cua he thong:
- POST /api/identify: nhan anh tu giao dien web va tra ve ket qua nhan dien
- GET /api/species: tim kiem va loc danh sach 3,570 loai cay
- GET /api/benchmarks: lay bang ket qua thuc nghiem va bieu do
"""
from __future__ import annotations

import io
import json
import random
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw

from configs.settings import (
    DATASET_ROOT,
    REPORTS_DIR,
    BENCHMARK_REPORT_PATH,
    EMBEDDINGS_META_PATH,
    WORD_REPORT_PART1_PATH,
    WORD_REPORT_PART2_PATH,
    WORD_REPORT_PATH,
)
from models.inference_engine import BioLensInferenceEngine

router = APIRouter(prefix="/api", tags=["BioLens API"])

_engine: Optional[BioLensInferenceEngine] = None


def get_engine() -> BioLensInferenceEngine:
    global _engine
    if _engine is None:
        _engine = BioLensInferenceEngine()
    return _engine


@router.post("/identify")
async def identify_uploaded_image(
    file: UploadFile = File(...),
    algorithm: str = Form("ensemble"),
    organ: str = Form("auto"),
):
    """Nhận diện ảnh người dùng tải lên hoặc chụp từ Camera WebRTC."""
    engine = get_engine()
    try:
        raw_bytes = await file.read()
        pil_img = Image.open(io.BytesIO(raw_bytes))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"File ảnh không hợp lệ: {exc}")

    result = engine.identify_image(
        pil_img=pil_img,
        algorithm=algorithm,
        organ_hint=organ,
        top_k=5,
    )
    return result


@router.post("/identify-demo")
async def identify_demo_specimen(
    mode: str = Query("plant", description="plant | ood_object | ood_blur"),
    species_key: Optional[str] = Query(None),
    algorithm: str = Query("ensemble"),
):
    """
    Hỗ trợ kiểm thử nhanh 1-click trên giao diện Web:
    - mode='plant'      : Lấy ngẫu nhiên (hoặc theo species_key) một ảnh hoa/cây thực tế từ dataset để nhận diện
    - mode='ood_object' : Tạo ảnh vật thể nhân tạo / hình học ngoài miền thực vật để kiểm chứng Bộ lọc OOD
    - mode='ood_blur'   : Tạo ảnh mờ/tối để kiểm chứng Tầng 0 (Image Quality Gate)
    """
    engine = get_engine()

    if mode == "ood_blur":
        img = Image.new("RGB", (320, 320), color=(10, 12, 10))
        res = engine.identify_image(img, algorithm=algorithm, organ_hint="auto")
        res["demoImageUrl"] = None
        res["demoDescription"] = "Ảnh mô phỏng ống kính bị che tối / mất nét (Kiểm thử Tầng 0)"
        return res

    if mode == "ood_object":
        # Tạo ảnh mô phỏng màn hình/giao diện kẻ ô nhân tạo để kiểm thử bộ lọc OOD
        arr = np.full((320, 320, 3), 235, dtype=np.uint8)
        arr[::32, :, :] = 40
        arr[:, ::32, :] = 40
        arr[80:240, 60:260] = [30, 80, 190]
        img = Image.fromarray(arr)
        res = engine.identify_image(img, algorithm=algorithm, organ_hint="auto")
        res["demoImageUrl"] = None
        res["demoDescription"] = "Ảnh vật thể nhân tạo / đồ họa máy tính (Kiểm thử Bộ lọc OOD)"
        return res

    # Chọn một loài có tên tiếng Việt rõ ràng để demo
    if species_key and species_key in engine.species_map:
        chosen_key = species_key
    else:
        vn_keys = [
            k
            for k, v in engine.species_map.items()
            if not v.get("primaryVietnameseName", "").startswith("Loài ")
            and v.get("totalImages", 0) >= 20
        ]
        chosen_key = random.choice(vn_keys if vn_keys else list(engine.species_map.keys()))

    sp_entry = engine.species_map[chosen_key]
    sample_paths = sp_entry.get("sampleImagePaths", [])
    if not sample_paths:
        raise HTTPException(status_code=404, detail="Không tìm thấy ảnh mẫu cho loài này.")

    chosen_rel = random.choice(sample_paths)
    full_img_path = DATASET_ROOT / chosen_rel
    with Image.open(full_img_path) as im:
        pil_copy = im.copy()

    res = engine.identify_image(pil_copy, algorithm=algorithm, organ_hint="auto")
    res["demoImageUrl"] = f"/api/image/{chosen_rel}"
    res["demoGroundTruth"] = {
        "speciesKey": chosen_key,
        "vietnameseName": sp_entry.get("primaryVietnameseName"),
        "canonicalName": sp_entry.get("canonicalName"),
        "family": sp_entry.get("family"),
    }
    return res


@router.get("/species")
async def list_and_search_species(
    q: str = Query("", description="Từ khóa tìm kiếm tên Tiếng Việt, tên Khoa học, hoặc speciesKey"),
    family: str = Query("", description="Lọc theo Họ thực vật (ví dụ: Fabaceae, Asteraceae, Malvaceae)"),
    kingdom: str = Query("", description="Lọc theo Giới (Plantae, Fungi...)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
):
    """Tra cứu bách khoa toàn thư 3,570 loài thực vật & nấm dược liệu Việt Nam."""
    engine = get_engine()
    q_norm = q.strip().lower()
    fam_norm = family.strip().lower()
    king_norm = kingdom.strip().lower()

    matched = []
    for s_key, item in engine.species_map.items():
        if king_norm and item.get("kingdom", "").lower() != king_norm:
            continue
        if fam_norm and item.get("family", "").lower() != fam_norm:
            continue
        if q_norm:
            vn_main = item.get("primaryVietnameseName", "").lower()
            vn_aliases = " ".join(item.get("vietnameseAliases", [])).lower()
            sci = item.get("scientificName", "").lower()
            en = item.get("vernacularNameEn", "").lower()
            fam_vn = item.get("familyVn", "").lower()
            if not (
                q_norm in s_key.lower()
                or q_norm in vn_main
                or q_norm in vn_aliases
                or q_norm in sci
                or q_norm in en
                or q_norm in fam_vn
            ):
                continue
        matched.append(item)

    # Ưu tiên hiển thị các loài có tên Tiếng Việt bản địa lên trước
    matched.sort(
        key=lambda x: (
            x.get("primaryVietnameseName", "").startswith("Loài "),
            -int(x.get("totalImages", 0)),
        )
    )

    total = len(matched)
    start = (page - 1) * page_size
    end = start + page_size
    slice_items = matched[start:end]

    formatted_items = []
    for it in slice_items:
        samples = it.get("sampleImagePaths", [])
        thumb_url = f"/api/image/{samples[0]}" if samples else None
        formatted_items.append(
            {
                **it,
                "thumbnailUrl": thumb_url,
            }
        )

    return {
        "totalMatched": total,
        "page": page,
        "pageSize": page_size,
        "totalPages": max(1, (total + page_size - 1) // page_size),
        "items": formatted_items,
        "topFamilies": engine.catalog_summary.get("topFamilies", []),
    }


@router.get("/species/{species_key}")
async def get_species_full_profile(species_key: str):
    """Lấy hồ sơ thực vật học & dược liệu chi tiết 6 mục của một loài."""
    engine = get_engine()
    if species_key not in engine.species_map and species_key not in engine.knowledge_map:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy loài với mã {species_key}")
    return engine.get_enriched_species_info(species_key, fetch_live_wiki=True)


@router.get("/image/{species_key}/{filename}")
async def serve_dataset_specimen_image(species_key: str, filename: str):
    """Phục vụ ảnh gốc từ thư mục dữ liệu E:\\VietMediSpecies2026\\<species_key>\\<filename>."""
    if not species_key.isdigit() or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Đường dẫn ảnh không hợp lệ.")
    img_path = DATASET_ROOT / species_key / filename
    if not img_path.exists() or not img_path.is_file():
        raise HTTPException(status_code=404, detail="Không tìm thấy file ảnh.")
    return FileResponse(img_path)


@router.get("/benchmarks")
async def get_ml_benchmarks_and_dataset_stats():
    """Trả về số liệu thống kê bộ dữ liệu và bảng so sánh thực nghiệm 4 mô hình Học máy."""
    engine = get_engine()
    engine.reload_models_if_needed()

    bench_data = {}
    if BENCHMARK_REPORT_PATH.exists():
        try:
            bench_data = json.loads(BENCHMARK_REPORT_PATH.read_text(encoding="utf-8"))
        except Exception:
            bench_data = {}

    extract_meta = {}
    if EMBEDDINGS_META_PATH.exists():
        try:
            extract_meta = json.loads(EMBEDDINGS_META_PATH.read_text(encoding="utf-8"))
        except Exception:
            extract_meta = {}

    charts_manifest = []
    manifest_path = REPORTS_DIR / "charts_manifest.json"
    if manifest_path.exists():
        try:
            charts_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            charts_manifest = []

    return {
        "catalogSummary": engine.catalog_summary,
        "extractionMeta": extract_meta,
        "benchmarkReport": bench_data,
        "chartsManifest": charts_manifest,
        "hasWordReport": WORD_REPORT_PATH.exists(),
        "wordReportUrl": "/api/download-report" if WORD_REPORT_PATH.exists() else None,
        "hasPart1Report": WORD_REPORT_PART1_PATH.exists(),
        "part1ReportUrl": "/api/download-report-v1" if WORD_REPORT_PART1_PATH.exists() else None,
        "hasPart2Report": WORD_REPORT_PART2_PATH.exists(),
        "part2ReportUrl": "/api/download-report" if WORD_REPORT_PART2_PATH.exists() else None,
    }


@router.get("/chart/{chart_name}")
async def serve_report_chart(chart_name: str):
    """Phục vụ trực tiếp 10 biểu đồ khoa học PNG cho giao diện Web."""
    if ".." in chart_name or "/" in chart_name or "\\" in chart_name or not chart_name.endswith(".png"):
        raise HTTPException(status_code=400, detail="Tên biểu đồ không hợp lệ.")
    chart_path = REPORTS_DIR / chart_name
    if not chart_path.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy biểu đồ.")
    return FileResponse(chart_path, media_type="image/png")


@router.get("/download-report")
async def download_word_report():
    """Tải trực tiếp file Báo cáo Đồ án Word Đầy đủ (Phần 1 + Phần 2 Fine-tuned, .docx)."""
    target_path = WORD_REPORT_PART2_PATH if WORD_REPORT_PART2_PATH.exists() else WORD_REPORT_PATH
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Báo cáo Word đang được khởi tạo.")
    return FileResponse(
        target_path,
        filename="Bao_Cao_Do_An_BioLens_Phan_2_Finetuned_Day_Du.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/download-report-v1")
async def download_word_report_v1():
    """Tải trực tiếp file Báo cáo Đồ án Bản cũ đã lưu trữ — Phần 1 (Baseline v1, .docx)."""
    if not WORD_REPORT_PART1_PATH.exists():
        raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo Phần 1 Baseline.")
    return FileResponse(
        WORD_REPORT_PART1_PATH,
        filename="Bao_Cao_Do_An_BioLens_Phan_1_Baseline.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
