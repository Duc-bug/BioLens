"""
File cau hinh chung cho project BioLens.
Luu duong dan den thu muc dataset, file csv metadata va cac tham so train mo hinh.
"""
from __future__ import annotations

import os
from pathlib import Path
import torch

# Duong dan den thu muc BioLens
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Tu dong nap bien moi truong tu file .env neu co
try:
    from dotenv import load_dotenv

    for _env_path in [
        PROJECT_ROOT / ".env",
        PROJECT_ROOT.parent / ".env",
    ]:
        if _env_path.exists():
            load_dotenv(_env_path)
            break
except Exception:
    pass

# Duong dan mac dinh: uu tien e:/VietMediSpecies2026/dataset neu ton tai
DEFAULT_DATASET_ROOT = (
    PROJECT_ROOT.parent / "dataset"
    if (PROJECT_ROOT.parent / "dataset").is_dir()
    else PROJECT_ROOT.parent
)

DATASET_ROOT = Path(os.getenv("BIOLENS_DATASET_ROOT", str(DEFAULT_DATASET_ROOT)))


def _resolve_metadata_path() -> Path:
    env_val = os.getenv("BIOLENS_METADATA_CSV")
    if env_val:
        p = Path(env_val)
        if p.exists():
            return p
    candidates = [
        DATASET_ROOT / "VietMediSpecies2026_metadata_dataset.csv",
        DATASET_ROOT.parent / "VietMediSpecies2026_metadata_dataset.csv",
        Path("E:/VietMediSpecies2026_metadata_dataset.csv"),
        PROJECT_ROOT.parent.parent / "VietMediSpecies2026_metadata_dataset.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    return DATASET_ROOT / "VietMediSpecies2026_metadata_dataset.csv"


METADATA_CSV_PATH = _resolve_metadata_path()

STORAGE_DIR = Path(os.getenv("BIOLENS_STORAGE_DIR", str(PROJECT_ROOT / "storage")))
CATALOG_DIR = STORAGE_DIR / "catalog"
EMBEDDINGS_DIR = STORAGE_DIR / "embeddings"
CHECKPOINTS_DIR = STORAGE_DIR / "checkpoints"
REPORTS_DIR = STORAGE_DIR / "reports"
V1_BASELINE_REPORT_DIR = REPORTS_DIR / "v1_baseline"
V2_FINETUNED_REPORT_DIR = REPORTS_DIR / "v2_finetuned"

for _dir in [
    STORAGE_DIR,
    CATALOG_DIR,
    EMBEDDINGS_DIR,
    CHECKPOINTS_DIR,
    REPORTS_DIR,
    V1_BASELINE_REPORT_DIR,
    V2_FINETUNED_REPORT_DIR,
]:
    _dir.mkdir(parents=True, exist_ok=True)

# 2. Đường dẫn các file Danh mục & Tri thức Thực vật học
SPECIES_CATALOG_PATH = CATALOG_DIR / "species_catalog.json"
DATASET_SPLITS_PATH = CATALOG_DIR / "dataset_splits.json"
SPECIES_KNOWLEDGE_PATH = CATALOG_DIR / "species_knowledge.json"
WIKI_CACHE_PATH = CATALOG_DIR / "wiki_cache.json"

# 3. Đường dẫn file Embeddings và Checkpoints (Hỗ trợ cả Baseline v1 & Fine-tuned v2)
EMBEDDINGS_MATRIX_PATH = EMBEDDINGS_DIR / "features_fp16.npy"
EMBEDDINGS_LABELS_PATH = EMBEDDINGS_DIR / "labels_int32.npy"
EMBEDDINGS_SPLITS_PATH = EMBEDDINGS_DIR / "splits_uint8.npy"
EMBEDDINGS_PATHS_PATH = EMBEDDINGS_DIR / "rel_paths.json"
EMBEDDINGS_META_PATH = EMBEDDINGS_DIR / "extraction_meta.json"

METRIC_ADAPTER_PATH = CHECKPOINTS_DIR / "botanical_metric_adapter_v2.pt"
PROTOTYPES_MODEL_PATH = CHECKPOINTS_DIR / "cosine_prototypes.npz"
KNN_INDEX_PATH = CHECKPOINTS_DIR / "weighted_knn_index.npz"
LINEAR_SVM_MODEL_PATH = CHECKPOINTS_DIR / "linear_svm_weights.npz"
MLP_CLASSIFIER_PATH = CHECKPOINTS_DIR / "cosine_mlp_model.pt"
OOD_CALIBRATION_PATH = CHECKPOINTS_DIR / "ood_calibration.json"

# 4. Đường dẫn Báo cáo Thực nghiệm (Lưu giữ Phần 1 Baseline & Phần 2 Fine-tuned)
V1_BENCHMARK_JSON_PATH = V1_BASELINE_REPORT_DIR / "ml_benchmark_results_v1_baseline.json"
BENCHMARK_REPORT_PATH = REPORTS_DIR / "ml_benchmark_results.json"

WORD_REPORT_PART1_PATH = REPORTS_DIR / "Bao_Cao_Do_An_BioLens_Phan_1_Baseline.docx"
WORD_REPORT_PART2_PATH = REPORTS_DIR / "Bao_Cao_Do_An_BioLens_Phan_2_Finetuned_Day_Du.docx"
WORD_REPORT_PATH = REPORTS_DIR / "Bao_Cao_Do_An_BioLens_Hoc_May_Va_Ung_Dung.docx"

# 5. Cấu hình Thiết bị & Trích xuất Đặc trưng
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
USE_FP16 = torch.cuda.is_available()
HARDWARE_LABEL = "CUDA GPU Acceleration (Mixed Precision FP16)" if torch.cuda.is_available() else "CPU Execution"

BACKBONE_NAME = "mobilenetv3_large_100"
IMAGE_SIZE = int(os.getenv("BIOLENS_IMAGE_SIZE", "224"))
BATCH_SIZE = int(os.getenv("BIOLENS_BATCH_SIZE", "256"))
NUM_WORKERS = int(os.getenv("BIOLENS_NUM_WORKERS", "4"))

_max_imgs_env = os.getenv("BIOLENS_MAX_IMAGES_PER_SPECIES", "").strip()
MAX_IMAGES_PER_SPECIES = (
    int(_max_imgs_env) if _max_imgs_env and _max_imgs_env != "0" else None
)
RANDOM_SEED = 42

TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
TEST_RATIO = 0.10

# 6. Cấu hình Bộ lọc Từ chối Nhận diện 2 Tầng (2-Stage OOD Rejection Gate)
MIN_BLUR_LAPLACIAN_VAR = 18.0
MIN_BRIGHTNESS = 15.0
MAX_BRIGHTNESS = 250.0
BOTANICAL_GATE_THRESHOLD = 0.36
MIN_COSINE_SIMILARITY = 0.42
MIN_CONFIDENCE_SCORE = 0.35

# 7. Cấu hình Server Web
HOST = os.getenv("BIOLENS_HOST", "127.0.0.1")
PORT = int(os.getenv("BIOLENS_PORT", "8000"))
