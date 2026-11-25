from __future__ import annotations

import os
from pathlib import Path
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    for _env_path in [PROJECT_ROOT / ".env", PROJECT_ROOT.parent / ".env"]:
        if _env_path.exists():
            load_dotenv(_env_path)
            break
except Exception:
    pass

DEFAULT_DATASET_ROOT = (
    PROJECT_ROOT.parent / "dataset"
    if (PROJECT_ROOT.parent / "dataset").is_dir()
    else PROJECT_ROOT.parent
)
DATASET_ROOT = Path(os.getenv("BIOLENS_DATASET_ROOT", str(DEFAULT_DATASET_ROOT)))


def _resolve_metadata_path() -> Path:
    env_val = os.getenv("BIOLENS_METADATA_CSV")
    if env_val and Path(env_val).exists():
        return Path(env_val)
    for c in [
        DATASET_ROOT / "VietMediSpecies2026_metadata_dataset.csv",
        DATASET_ROOT.parent / "VietMediSpecies2026_metadata_dataset.csv",
        Path("E:/VietMediSpecies2026_metadata_dataset.csv"),
    ]:
        if c.exists():
            return c
    return DATASET_ROOT / "VietMediSpecies2026_metadata_dataset.csv"


METADATA_CSV_PATH = _resolve_metadata_path()

STORAGE_DIR = Path(os.getenv("BIOLENS_STORAGE_DIR", str(PROJECT_ROOT / "storage")))
CATALOG_DIR = STORAGE_DIR / "catalog"
EMBEDDINGS_DIR = STORAGE_DIR / "embeddings"
CHECKPOINTS_DIR = STORAGE_DIR / "checkpoints"
REPORTS_DIR = STORAGE_DIR / "reports"

for _dir in [STORAGE_DIR, CATALOG_DIR, EMBEDDINGS_DIR, CHECKPOINTS_DIR, REPORTS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# Danh mục & Tri thức Thực vật học
SPECIES_CATALOG_PATH = CATALOG_DIR / "species_catalog.json"
DATASET_SPLITS_PATH = CATALOG_DIR / "dataset_splits.json"
SPECIES_KNOWLEDGE_PATH = CATALOG_DIR / "species_knowledge.json"
WIKI_CACHE_PATH = CATALOG_DIR / "wiki_cache.json"

# Embeddings và Checkpoints của BioCLIP 2 (768 chiều)
EMBEDDINGS_MATRIX_PATH = EMBEDDINGS_DIR / "features_bioclip2_fp16.npy"
EMBEDDINGS_LABELS_PATH = EMBEDDINGS_DIR / "labels_bioclip2_int32.npy"
EMBEDDINGS_SPLITS_PATH = EMBEDDINGS_DIR / "splits_bioclip2_uint8.npy"
EMBEDDINGS_PATHS_PATH = EMBEDDINGS_DIR / "rel_paths_bioclip2.json"
EMBEDDINGS_META_PATH = EMBEDDINGS_DIR / "extraction_meta.json"
SPECIES_TEXT_EMB_PATH = EMBEDDINGS_DIR / "species_text_embeddings.npy"

DOMAIN_TEXT_EMB_PATH = CHECKPOINTS_DIR / "ood_domain_text_embeddings.npz"
CLASSIFIER_MODEL_PATH = CHECKPOINTS_DIR / "bioclip2_classifier.pt"
PROTOTYPES_MODEL_PATH = CHECKPOINTS_DIR / "cosine_prototypes.npz"
OOD_CALIBRATION_PATH = CHECKPOINTS_DIR / "ood_calibration.json"

# Báo cáo thực nghiệm
BENCHMARK_REPORT_PATH = REPORTS_DIR / "ml_benchmark_results.json"
WORD_REPORT_PATH = PROJECT_ROOT / "docs" / "Bao_Cao_Toan_Tap_BioLens_Vietnam_VLU.docx"

# Cấu hình Mô hình nền duy nhất: BioCLIP 2 (ViT-L/14, TreeOfLife-200M)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
USE_FP16 = torch.cuda.is_available()
HARDWARE_LABEL = "CUDA GPU Acceleration (Mixed Precision FP16)" if torch.cuda.is_available() else "CPU Execution"

BIOCLIP_MODEL_ID = os.getenv("BIOLENS_MODEL_ID", "hf-hub:imageomics/bioclip-2")
BACKBONE_NAME = "bioclip-2 (ViT-L/14, TreeOfLife-200M)"
IMAGE_SIZE = int(os.getenv("BIOLENS_IMAGE_SIZE", "224"))
BATCH_SIZE = int(os.getenv("BIOLENS_BATCH_SIZE", "128"))
NUM_WORKERS = int(os.getenv("BIOLENS_NUM_WORKERS", "6"))
USE_FLIP_TTA = os.getenv("BIOLENS_USE_FLIP_TTA", "1").strip() != "0"

_max_imgs_env = os.getenv("BIOLENS_MAX_IMAGES_PER_SPECIES", "").strip()
MAX_IMAGES_PER_SPECIES = (
    int(_max_imgs_env) if _max_imgs_env and _max_imgs_env != "0" else None
)
RANDOM_SEED = 42

TRAIN_RATIO = 0.80
VAL_RATIO = 0.10
TEST_RATIO = 0.10

# Ngưỡng kiểm tra chất lượng ảnh & bộ lọc OOD
MIN_BLUR_LAPLACIAN_VAR = 18.0
MIN_BRIGHTNESS = 15.0
MAX_BRIGHTNESS = 250.0
BOTANICAL_GATE_THRESHOLD = 0.45
MIN_COSINE_SIMILARITY = 0.35
MIN_CONFIDENCE_SCORE = 0.30

HOST = os.getenv("BIOLENS_HOST", "127.0.0.1")
PORT = int(os.getenv("BIOLENS_PORT", "8000"))
